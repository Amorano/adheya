"""."""

import os
import sys
import json
from importlib import import_module
from inspect import isclass
from dearpygui import core, simple
from adheya import DPGObject, CallbackType
from adheya.node import Node

class NodeEditor(DPGObject):

	_CYCLECHECK = True

	def __init__(self, **kw):
		super().__init__(None, **kw)

		# command factory to make node *
		self.__nodeMap = {}
		self.__nodes = {}
		self.__links = {}
		self.__root = os.path.dirname(os.path.realpath(__file__))

		parent = self.parent.guid
		paneleft = f'{self.guid}-paneleft'
		paneright = f'{self.guid}-paneright'

		with simple.group(paneleft, parent=parent, width=100):
			with simple.group(f"{paneleft}-control"):
				core.add_button(f"{paneleft}-control.save", label="save", callback=self.__save, width=90, height=25)
				core.add_same_line()
				core.add_button(f"{paneleft}-control.load", label="load", callback=self.__load, width=90, height=25)

			with simple.node_editor(self.guid, link_callback=self.__link, delink_callback=self.__delink):
				...

		core.add_same_line(parent=parent)

		with simple.group(paneright, parent=parent, width=500):
			with simple.group(f"{paneright}-inspector"):
				core.add_button(f"{paneright}-control.save", label="save", callback=self.__save, width=90, height=25)
				core.add_same_line()
				core.add_button(f"{paneright}-control.load", label="load", callback=self.__load, width=90, height=25)

		self.register("adheya.nodeLib")
		self.parent.register(CallbackType.MouseClick, self.__mouseClick)

	def __mouseClick(self, sender, data):
		# if you there is a way to do combined individual attrs and grouped?
		nodes = core.get_selected_nodes(self.guid)
		width = 400 if len(nodes) > 0 else 0
		core.configure_item(f'{self.guid}-paneright', width=width)
		for n in nodes:
			for attr in self.__nodes[n].inputs:
				print(attr)

	def __nodelistRefresh(self):
		nodelist = f"{self.guid}-nodelist"
		if nodelist in core.get_all_items():
			core.delete_item(nodelist)

		with simple.popup(self.guid, nodelist, parent="main"):
			for k in self.registryNodes:
				core.add_text(k, default_value=k)
				for obj in self.registry(k):
					name = getattr(obj, '_name', obj.__name__)
					core.add_button(obj.__name__,
						label=name, width=60, height=15,
						callback=self.__nodeAdd, callback_data=obj)

	def __nodeAdd(self, sender, obj):
		core.close_popup(f"{self.guid}-nodelist")
		size = core.get_item_rect_min(sender)
		# weak sauce hardcoded offset
		x = max(0, int(size[0]) - 140)
		y = max(0, int(size[1]) - 40)
		label = getattr(obj, '_name', obj.__class__.__name__)
		# print(label, obj)
		node = obj(None, parent=self.guid, label=label, x_pos=x, y_pos=y)
		self.__nodes[node.guid] = node

	def registry(self, index):
		return self.__nodeMap[index]

	def register(self, module):
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
			self.__nodeMap[cat] = data

		self.__nodelistRefresh()

	@property
	def registryNodes(self):
		return [k for k in sorted(self.__nodeMap.keys()) if k != '_']

	@property
	def nodes(self):
		return self.__nodes.copy()

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
