"""."""

import os
import sys
import json
from enum import Enum
from importlib import import_module
from inspect import isclass
from dearpygui import core, simple
from adheya import DPGObject, CallbackType, Registry
from adheya.feedback import Label
from adheya.general import NumericSlider, Button
from adheya.layout import Group, SpacingVertical
from adheya.win import Window

def fileDotName(file: str, root: str) -> str:
	path, _ = os.path.splitext(file)
	name = os.path.abspath(path).replace(root, '')
	name = name.replace(os.sep, '.').replace('__init__', '')
	return name.strip('.')

class PlugDirection(Enum):
	Input = 0
	Output = 1
	Static = 2

	@staticmethod
	def filter(node):
		config = core.get_item_configuration(node)
		if config.get('output', None):
			return PlugDirection.Output
		if config.get('static', None):
			return PlugDirection.Static
		return PlugDirection.Input

class NodeAttribute(DPGObject):
	def __init__(self, parent, plug, plugDir, attr, attrType, **kw):
		super().__init__(parent, **kw)
		self.__type = attrType
		self.__attr = attr
		self.__plugDir = plugDir

		output = plugDir == PlugDirection.Output
		static = plugDir == PlugDirection.Static

		core.add_node_attribute(plug, parent=self.parent.guid, output=output, static=static)
		# mapped command to create plug inside this attribute wrapper
		kw['width'] = kw.get('width', 80)
		kw['label'] = kw.get('label', attr)
		self.__widget = attrType(plug, **kw)
		core.end()

	@property
	def attrType(self):
		return self.__type

	@property
	def attr(self):
		return self.__attr

	@property
	def plugDir(self):
		return self.__plugDir

	def event(self, event, *arg, **kw):
		if self.__widget:
			self.__widget.event(event, *arg, **kw)

class Node(DPGObject):
	def __init__(self, parent, **kw):
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
		super().__init__(parent, **kw)

		self.__attrInput = {}
		self.__attrOutput = {}
		self.__attrStatic = {}

		kw['parent'] = self.parent.guid

		with simple.node(self.guid, **kw):
			...

	def event(self, event, *arg, **kw):
		"""Cast the event to all the attributes."""
		for callback in (self.__attrInput, self.__attrStatic, self.__attrOutput):
			for cb in callback.values():
				cb.event(event, *arg, **kw)

	def calculate(self):
		"""Propagates the value based on depth first."""
		return True

	def attrAdd(self, name, attrType, plugDir: PlugDirection=PlugDirection.Input, **kw) -> NodeAttribute:
		if self.guid in self.__attrOutput or self.guid in self.__attrInput or self.guid in self.__attrStatic:
			raise Exception(f"Attribute {name} already exists")

		attr = [self.__attrInput, self.__attrOutput, self.__attrStatic][plugDir.value]

		# the outside wrapper and thing which DPG connects
		plugname = f"{self.guid}-{name}"

		# the actual attribute where the value is held
		attrname = f"{plugname}.attr"
		kw.pop('static', None)
		kw.pop('output', None)
		kw.pop('parent', None)
		kw['label'] = kw.get('label', name)
		na = NodeAttribute(self.guid, plugname, plugDir, attrname, attrType, **kw)
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
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		self.__slider = NumericSlider(self, label='', width=1,
			default_value=1, min_value=0, max_value=3, clamped=True,
			callback=lambda s, d: self.__zoom())

		self.register(CallbackType.Resize, self.__resize)
		self.__resize(self, None)

	def __resize(self, sender, data):
		w, _ = self.parent.size
		w = int(min(max(w, 16), 256))
		self.__slider.width = w
		# core.configure_item(self.__idGroup, width=w)

	def __zoom(self):
		self.event('zoom', self.__slider.value)

	@property
	def zoomLevel(self):
		return self.__slider.value

class NodeEditor(DPGObject):

	_CYCLECHECK = True

	def __init__(self, parent, *arg, **kw):
		super().__init__(parent, *arg, **kw)

		# command factory to make node *
		self.__inspector = None
		self.__nodeMap = {}
		self.__nodes = {}
		self.__links = {}
		self.__root = os.path.dirname(os.path.abspath(__file__))
		self.__paneRight = Window(no_title_bar=True)

		m = self.mainbar.add('file')
		m.addItem('load', callback=self.__load)
		m.addItem('save', callback=self.__save)

		with simple.node_editor(self.guid, parent=self.parent.guid, link_callback=self.__link, delink_callback=self.__delink):
			...

		kw['no_close'] = kw['no_collapse'] = kw['no_title_bar'] = kw['no_focus_on_appearing'] = True
		kw['autosize'] = False
		kw.pop('parent', None)

		self.libImportDir(f'{self.__root}/nodeLib')
		self.register(CallbackType.Resize, self.__resize)
		self.register(CallbackType.MouseRelease, self.__resize)

	def __resize(self, sender, data):
		if self.__paneRight is None:
			return
		w, h = core.get_main_window_size()
		width = self.__paneRight.width
		width = min(max(width, 0), int(w * .25))
		self.__paneRight.configure(height=h - 25, width=width, y_pos=-1, x_pos=w - width + 25)
		nodes = core.get_selected_nodes(self.guid) or []
		if len(nodes) == 0:
			self.__paneRight.show = False
			return
		self.__paneRight.show = True
		nodes = [self.__nodes[n] for n in nodes]

		if self.__inspector:
			self.__inspector.delete()
		self.__inspector = Group(self.__paneRight)

		for n in nodes:
			sub = Group(self.__inspector)
			Label(sub, default_value=n.label)
			for guid, _ in n.inputs.items():
				val = str(core.get_value(guid))
				Label(sub, default_value=val)

			for _ in range(7):
				SpacingVertical(self.__inspector)

	def __nodelistRefresh(self):
		nodeList = f"{self.guid}-nodelist"
		del Registry[nodeList]

		kw = {'width': 60, 'height': 15, 'callback': self.__nodeAdd}
		with simple.popup(self.guid, nodeList):
			...

		for k in sorted(self.registryNodes):
			Label(nodeList, default_value=k)
			for obj in self.__nodeMap[k]:
				name = getattr(obj, '_name', obj.__name__)
				Button(nodeList, label=name, callback_data=obj, **kw)

	def __nodeAdd(self, sender, obj):
		size = core.get_item_rect_min(sender)
		# weak sauce hardcoded offset
		x = max(0, int(size[0]) - 140)
		y = max(0, int(size[1]) - 40)
		label = getattr(obj, '_name', obj.__class__.__name__)
		node = obj(self.guid, label=label, x_pos=x, y_pos=y)
		self.__nodes[node.guid] = node

	def __delink(self, sender, data):
		# nodes attributes are in left->right order
		attr1, attr2 = data
		left = attr1.split('-')[0]
		right = attr2.split('-')[0]

		try:
			data = self.__links[left]
		except Exception as e:
			print(e)
			core.log_error(e)
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

	@property
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
	# >> NODE GRAPH
	# ============================================
	def dfs(self, v, visited):
		"""Depth First Search."""
		# Mark current node visited
		visited.add(v)

		# Recurse all the vertices adjacent to this vertex
		for neighbor in self.__links.get(v, []):
			if neighbor not in visited:
				self.dfs(neighbor, visited)

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
