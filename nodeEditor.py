"""."""

import os
import sys
import json
from importlib import import_module
from inspect import isclass
from dearpygui import core, simple
from adheya import DPGObject, CallbackType
from adheya.node import Node
from adheya.general import Label

class NodeEditor(DPGObject):

	_CYCLECHECK = True

	def __init__(self, parent, **kw):
		kw['parent'] = parent
		super().__init__(None, **kw)

		# command factory to make node *
		self.__nodeMap = {}
		self.__nodes = {}
		self.__links = {}
		self.__root = os.path.dirname(os.path.realpath(__file__))

		m = self.menubar.add('file')
		m.add('load', callback=self.__load)
		m.add('save', callback=self.__save)

		with simple.node_editor(self.guid, parent=self.parent.guid, link_callback=self.__link, delink_callback=self.__delink):
			...

		core.add_same_line(parent=self.parent.guid)

		paneright = f'{self.guid}-paneright'
		with simple.window(paneright,
				no_close=True,
				autosize=False,
				no_collapse=True,
				no_title_bar=True,
				no_focus_on_appearing=True,
			):
				with simple.group(f"{paneright}-inspector", parent=paneright):
					...

		# placeholder for all context menu popups since we cant figure out what things we are over?
		self.__idNodeList = f"{self.guid}-nodelist"
		with simple.popup(self.guid, self.__idNodeList, parent=self.guid):
			...

		self.libImport("adheya.nodeLib.nodeCore")
		self.libImport("adheya.nodeLib.nodeMath")
		self.libImport("adheya.nodeLib.nodeImage")

		# self.register(CallbackType.MouseClick, self.__mouseClick)
		self.register(CallbackType.Resize, self.__resize)
		# self.register(CallbackType.MouseDrag, self.__drag)
		self.register(CallbackType.MouseRelease, self.__resize)

	def __resize(self, sender, data):
		paneright = f'{self.guid}-paneright'
		w, h = core.get_main_window_size()
		width = core.get_item_configuration(paneright)["width"]
		width = min(max(width, 0), int(w * .25))
		core.configure_item(paneright, height=h - 25, width=width, y_pos=-1, x_pos=w - width + 25)
		nodes = core.get_selected_nodes(self.guid) or []
		if len(nodes) == 0:
			simple.hide_item(paneright)
			return
		simple.show_item(paneright)

		if "inspector" in core.get_all_items():
			core.delete_item("inspector")

		with simple.group("inspector", parent=paneright):
			for n in nodes:
				n = self.__nodes[n]
				inputs = n.inputs
				inspector = f"spect-{n}"
				with simple.group(inspector):
					core.add_text(n.label)
					for guid, attr in inputs.items():
						label = f"{inspector}-{attr.label}"
						val = str(core.get_value(guid))
						Label(label, label=attr.label, parent=inspector, default_value=val)

				for _ in range(10):
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
			print(str(e))
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
				print("Nodes cannot be cyclic")
				return

		data = self.__links.get(left, [])
		data.append(right)
		self.__links[left] = data

		# node = right.split('-')[0]
		# needs to call the dag list of edges from this node...
		visited = set()
		self.dfs(left, visited)
		for v in visited:
			if not self.__nodes[v].calculate():
				break

	def __save(self):
		fp = f'{self.__root}/nodes.json'
		with open(fp, 'w') as fp:
			for node in self.__nodes:
				print(node)
				print('-' * 30)
				for link in self.__links.get(node, []):
					print(link)
				print('=' * 80)

	def __load(self):
		fp = f'{self.__root}/nodes.json'
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
	def libImport(self, module):
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

		self.__nodelistRefresh()

	def registry(self, index):
		return self.__nodeMap[index]
