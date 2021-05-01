"""."""

import os
import sys
import json
from enum import Enum
from importlib import import_module
from inspect import isclass
from dearpygui import core, simple
from adheya import DPGObject, CallbackType
from adheya.feedback import Label
from adheya.general import FileHandle, FileImage, Numeric, InputType

def fileDotName(file: str, root: str) -> str:
	path, _ = os.path.splitext(file)
	name = os.path.abspath(path).replace(root, '')
	name = name.replace(os.sep, '.').replace('__init__', '')
	return name.strip('.')

class PlugType(Enum):
	Input = 0
	Output = 1
	Static = 2

	@staticmethod
	def filter(node):
		config = core.get_item_configuration(node)
		if config.get('output', None):
			return PlugType.Output
		if config.get('static', None):
			return PlugType.Static
		return PlugType.Input

class AttributeType(Enum):
	Bool = 0
	Int1 = 1
	Int2 = 2
	Int3 = 3
	Int4 = 4
	Float1 = 5
	Float2 = 6
	Float3 = 7
	Float4 = 8
	Color3 = 9
	Color4 = 10
	Pick3 = 11
	Pick4 = 12
	String = 13
	Button = 14
	Label = 15
	FileHandle = 16
	FileImage = 17

class NodeAttribute(DPGObject):
	_ATTRMAP = {
		AttributeType.Bool: core.add_checkbox,
		AttributeType.Int1: core.add_input_int,
		AttributeType.Int2: core.add_input_int2,
		AttributeType.Int3: core.add_input_int3,
		AttributeType.Int4: core.add_input_int4,
		AttributeType.Float1: core.add_input_float,
		AttributeType.Float2: core.add_input_float2,
		AttributeType.Float3: core.add_input_float3,
		AttributeType.Float4: core.add_input_float4,
		AttributeType.Color3: core.add_color_edit3,
		AttributeType.Color4: core.add_color_edit4,
		AttributeType.Pick3: core.add_color_picker3,
		AttributeType.Pick4: core.add_color_picker4,
		AttributeType.String: core.add_input_text,
		AttributeType.Button: core.add_button,
		AttributeType.Label: Label,
		AttributeType.FileHandle: FileHandle,
		AttributeType.FileImage: FileImage
	}

	def __init__(self, parent, plug, plugType, attr, attrType, **kw):
		kw['parent'] = parent
		super().__init__(plug, **kw)
		self.__type = attrType
		self.__attr = attr
		self.__plugType = plugType

		output = plugType == PlugType.Output
		static = plugType == PlugType.Static

		with simple.node_attribute(plug, parent=parent, output=output, static=static):
			# mapped command to create plug inside this attribute wrapper
			kw['parent'] = self.guid
			kw['width'] = kw.get('width', 80)
			self.__widget = self._ATTRMAP[attrType](attr, **kw)

	@property
	def attrType(self):
		return self.__type

	@property
	def attr(self):
		return self.__attr

	@property
	def plugType(self):
		return self.__plugType

	def event(self, event, *arg, **kw):
		if self.__widget:
			self.__widget.event(event, *arg, **kw)

class Node(DPGObject):
	def __init__(self, guid, **kw):
		"""Everything.

		[Node_index]-attr.[index]

		INPUTS:
			"guid": {
				# label
				'*': 'out',
				# type of plug
				"_": 1
			}

		OUTPUTS:
			"guid": {
				# label
				'*': 'out',
				# type of plug
				"_": 1,
				# links
				"+": []
			}
		"""
		super().__init__(guid, **kw)

		self.__attrInput = {}
		self.__attrOutput = {}
		self.__attrStatic = {}

		with simple.node(self.guid, **kw):
			...

	def event(self, event, *arg, **kw):
		"""Cast the event to all the attributes."""
		for callback in (self.__attrInput, self.__attrStatic, self.__attrOutput):
			for cb in callback.values():
				cb.event(event, *arg, **kw)

	def calculate(self):
		"""Propigates the value based on depth first."""
		return True

	def attrAdd(self, guid, attrType: AttributeType, plugType: PlugType=PlugType.Input, **kw) -> NodeAttribute:
		if guid in self.__attrOutput or guid in self.__attrInput or guid in self.__attrStatic:
			raise Exception(f"Attribute {guid} already exists")

		attr = [self.__attrInput, self.__attrOutput, self.__attrStatic][plugType.value]

		# the outside wrapper and thing which DPG connects
		plugname = f"{self.guid}-{guid}"

		# the actual attribute where the value is held
		attrname = f"{plugname}.attr"
		kw['label'] = kw.get('label', guid)
		kw.pop('static', None)
		kw.pop('output', None)
		kw.pop('parent', None)
		na = NodeAttribute(self.guid, plugname, plugType, attrname, attrType, **kw)
		attr[attrname] = na
		return na

	@property
	def outputs(self):
		return self.__attrOut.copy()

	@property
	def inputs(self):
		return self.__attrInput.copy()

	@property
	def dump(self):
		for i in self.__attrInput:
			print(i)

class NodeZoom(Node):
	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		self.__idGroup = f"{self.guid}-group"
		with simple.group(self.__idGroup, parent=self.guid):
			...

		self.__slider = Numeric(f"{self.guid}-zoom", label='', parent=self.__idGroup, width=1,
			inputType=InputType.Slider, default_value=1, min_value=0, max_value=3, clamped=True,
			callback=lambda s, d: self.__zoom())

		self.register(CallbackType.Resize, self.__resize)
		self.__resize(self, None)

	def __resize(self, sender, data):
		w, _ = self.parent.size
		w = int(min(max(w, 16), 256))
		core.configure_item(self.__idGroup, width=w)

	def __zoom(self):
		self.event('zoom', self.__slider.value)

	@property
	def zoomLevel(self):
		return self.__slider.value

class NodeEditor(DPGObject):

	_CYCLECHECK = True

	def __init__(self, parent, **kw):
		kw['parent'] = parent
		super().__init__(None, **kw)

		# command factory to make node *
		self.__nodeMap = {}
		self.__nodes = {}
		self.__links = {}
		self.__root = os.path.dirname(os.path.abspath(__file__))

		m = self.menubar.add('file')
		m.add('load', callback=self.__load)
		m.add('save', callback=self.__save)

		with simple.node_editor(self.guid, parent=self.parent.guid, link_callback=self.__link, delink_callback=self.__delink):
			...

		core.add_same_line(parent=self.parent.guid)

		self.__paneright = f'{self.guid}-paneright'
		kw['no_close'] = kw['no_collapse'] = kw['no_title_bar'] = kw['no_focus_on_appearing'] = True
		kw['autosize'] = False
		kw.pop('parent', None)
		with simple.window(self.__paneright, **kw):
			...

		# placeholder for all context menu popups since we cant figure out what things we are over?
		self.__idNodeList = f"{self.guid}-nodelist"
		with simple.popup(self.guid, self.__idNodeList, parent=self.guid):
			...

		self.libImportDir(f'{self.__root}/nodeLib')

		self.register(CallbackType.Resize, self.__resize)
		self.register(CallbackType.MouseRelease, self.__resize)

	def __resize(self, sender, data):
		w, h = core.get_main_window_size()
		width = core.get_item_configuration(self.__paneright)["width"]
		width = min(max(width, 0), int(w * .25))
		core.configure_item(self.__paneright, height=h - 25, width=width, y_pos=-1, x_pos=w - width + 25)
		nodes = core.get_selected_nodes(self.guid) or []
		if len(nodes) == 0:
			simple.hide_item(self.__paneright)
			return
		simple.show_item(self.__paneright)
		nodes = [self.__nodes[n] for n in nodes]

		DPGObject.delete("inspector")
		with simple.group("inspector", parent=self.__paneright):
			for n in nodes:
				inputs = n.inputs
				inspector = f"spect-{n}"
				# each widget...
				with simple.group(inspector, parent="inspector"):
					core.add_text(n.label)
					for guid, attr in inputs.items():
						label = f"{inspector}-{attr.label}"
						val = str(core.get_value(guid))
						Label(label, label=attr.label, parent=inspector, default_value=val)

				for _ in range(5):
					core.add_spacing()

	def __nodelistRefresh(self):
		children = core.get_item_children(self.__idNodeList)
		for item in children or []:
			core.delete_item(item)

		for k in sorted(self.registryNodes):
			core.add_text(k, default_value=k, parent=self.__idNodeList)
			for obj in self.__nodeMap[k]:
				name = getattr(obj, '_name', obj.__name__)
				core.add_button(obj.__name__, parent=self.__idNodeList,
					label=name, width=60, height=15,
					callback=self.__nodeAdd, callback_data=obj)

	def __nodeAdd(self, sender, obj):
		core.close_popup(self.__idNodeList)
		size = core.get_item_rect_min(sender)
		# weak sauce hardcoded offset
		x = max(0, int(size[0]) - 140)
		y = max(0, int(size[1]) - 40)
		label = getattr(obj, '_name', obj.__class__.__name__)
		node = obj(None, parent=self.guid, label=label, x_pos=x, y_pos=y)
		self.__nodes[node.guid] = node

	def __delink(self, sender, data):
		# nodes attributes are in left->right order
		attr1, attr2 = data
		left = attr1.split('-')[0]
		right = attr2.split('-')[0]

		try:
			data = self.__links[left]
		except Exception as e:
			core.log_error(str(e))
		else:
			if right in data:
				data.remove(right)
				self.__links[left] = data

	def __link(self, sender, data):
		# nodes attributes are in left->right order
		attr1, attr2 = data
		left = attr1.split('-')[0]
		right = attr2.split('-')[0]

		# if someone wanted to make a circuit simulator, you'd need cycles
		if self._CYCLECHECK:
			# but need to be A cyclic
			visited = set()
			self.dfs(right, visited)
			if left in visited:
				# delink in DPG and exit
				core.delete_node_link(self.guid, attr1, attr2)
				core.log_warning("Nodes cannot be cyclic")
				return

		data = self.__links.get(left, [])
		data.append(right)
		self.__links[left] = data

		# needs to call the dag list of edges from this node...
		visited = set()
		self.dfs(left, visited)
		for v in visited:
			print(v)
			calc = self.__nodes[v].calculate
			print(calc)
			if not calc():
				break
		print(456)

	def __save(self):
		fp = os.path.join(self.__root, 'nodes.json')
		with open(fp, 'w') as fp:
			# push all the nodes to the stack first, so the links all match up in the end.

			for node in self.__nodes:
				fp.write(node.dump)
			# now the links
			fp.write('link')
			for node in self.__nodes:
				for link in self.__links.get(node, []):
					fp.write(link)

	def __load(self):
		fp = os.path.join(self.__root, 'nodes.json')
		if not os.path.exists(fp):
			return
		with open(fp, 'r') as fp:
			data = json.load(fp)
		print(data)

	@property
	def registryNodes(self):
		return [k for k in sorted(self.__nodeMap.keys()) if k != '_']

	@property
	def nodes(self):
		return self.__nodes.copy()

	# ============================================
	# >> NODE GRAPH
	# ============================================
	def dfs(self, v, visited):
		"""Depth First Search."""
		# Mark current node visited
		visited.add(v)

		# Recurse all the vertices adjacent to this vertex
		for neighbour in self.__links.get(v, []):
			if neighbour not in visited:
				self.dfs(neighbour, visited)

	def all(self):
		"""Transverse the entire graph."""
		# Store all visited vertices
		visited = set()
		# Call DFS to iterate against all nodes
		for vertex in self.__links:
			if vertex not in visited:
				self.dfs(vertex, visited)
		return visited

	# ============================================
	# >> NODE DATABASE
	# ============================================
	def libImport(self, module, refresh=True):
		"""Parse module for Node* classes."""
		if isinstance(module, str):
			try:
				module = sys.modules[module]
			except KeyError as _:
				module = import_module(module)

		for obj in module.__dict__.values():
			if not isclass(obj) or not issubclass(obj, Node):
				continue

			cat = getattr(obj, '_category', '_')
			data = self.__nodeMap.get(cat, [])
			data.append(obj)
			self.__nodeMap[cat] = sorted(data, key=lambda o: getattr(o, '_name', o.__name__))

		if refresh:
			self.__nodelistRefresh()

	def libImportDir(self, path, recurse=True):
		root = os.sep.join(self.__root.split(os.path.sep)[:-1])
		for item in os.listdir(path):
			full = os.path.normpath(os.path.join(path, item))
			if recurse and os.path.isdir(item):
				self.libImportDir(full)
			elif full.endswith('.py') and os.path.isfile(full):
				full = fileDotName(full, root)
				self.libImport(full, refresh=False)

		self.__nodelistRefresh()

	def registry(self, index):
		return self.__nodeMap[index]
