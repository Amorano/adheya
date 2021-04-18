"""."""

import os
import sys
import json
from importlib import import_module
from enum import Enum
from inspect import isclass
from dearpygui import core, simple
from dpgo import DPGObject

class DirectionType(Enum):
	Output = 1
	Static = 2
	Input = 3

	@staticmethod
	def filter(node):
		config = core.get_item_configuration(node)
		if config.get('output', None):
			return DirectionType.Output
		if config.get('static', None):
			return DirectionType.Static
		return DirectionType.Input

class AttributeType(Enum):
	Bool = 1
	Int1 = 2
	Int2 = 3
	Int3 = 4
	Int4 = 5
	Float1 = 6
	Float2 = 7
	Float3 = 8
	Float4 = 9
	String = 10
	Label = 11

class Label(DPGObject):
	def __init__(self, name, **kw):
		super().__init__(name, **kw)
		with simple.group(f'{self.guid}-group', parent=self.parent):
			core.add_text(f'{self.guid}-label', default_value=self.prettyname)
			core.add_same_line()
			core.add_text(f'{self.guid}-text', default_value=' ')

	@property
	def label(self):
		return core.get_value(f'{self.guid}-label')

	@label.setter
	def label(self, val):
		core.set_value(f'{self.guid}-label', val)

	@property
	def value(self):
		return core.get_value(f'{self.guid}-text')

	@value.setter
	def value(self, val):
		core.set_value(f'{self.guid}-text', val)

class Node(DPGObject):
	_MAP = {
		AttributeType.Bool: core.add_checkbox,
		AttributeType.Int1: core.add_input_int,
		AttributeType.Int2: core.add_input_int2,
		AttributeType.Int3: core.add_input_int3,
		AttributeType.Int4: core.add_input_int4,
		AttributeType.Float1: core.add_input_float,
		AttributeType.Float2: core.add_input_float2,
		AttributeType.Float3: core.add_input_float3,
		AttributeType.Float4: core.add_input_float4,
		AttributeType.String: core.add_input_text,
		AttributeType.Label: Label
	}

	def __init__(self, name, **kw):
		# [Node_index]-attr.[index]
		super().__init__(name, **kw)

		self.__attr = {
			"_i": {},
			"_o": {}
		}

		with simple.node(self.guid, **kw):
			...
		"""{
			"<": {
				"a": 1,
				"b": 1,
			},
			">": {
				"out": {
					"_": 1,
					"+": []
				},
			}
		}"""

	def __getattr__(self, attr):
		return self.get(attr)

	def calculate(self):
		"""Propigates the value based on depth first."""
		path = set()
		self.parent.dfs(self.guid, path)
		for p in path:
			p.calculate()

	def __attrHelper(self, index, name, attrType: AttributeType, **kw):
		if name in self.__attr[index]:
			raise Exception(f"Attribute {name} already exists")

		# the outside wrapper and thing which DPG connects
		attr = f"{self.guid}-{name}"

		# the actual attribute where the value is held
		raw = f"{attr}.attr"
		kw['label'] = kw.get('label', name)
		kw['width'] = kw.get('width', 80)
		kw['parent'] = attr

		with simple.node_attribute(attr, parent=self.guid, output=(index == '_o')):
			# run the mapped command to create XYZ widget
			self._MAP[attrType](raw, **kw)

		self.__attr[index][raw] = {
		}

	def attrAddOut(self, name, attrType: AttributeType, **kw):
		self.__attrHelper('_o', name, attrType, **kw)

	def attrAddIn(self, name, attrType: AttributeType, **kw):
		self.__attrHelper('_i', name, attrType, **kw)

	@property
	def outputs(self):
		return self.__attr['_o'].copy()

	@property
	def inputs(self):
		return self.__attr['_i'].copy()

class NodeEditor(DPGObject):

	_CYCLECHECK = True

	def __init__(self, **kw):
		super().__init__(None, **kw)

		# command factory to make node *
		self.__nodeMap = {}
		self.__nodes = {}
		self.__links = {}
		self.__root = os.path.dirname(os.path.realpath(__file__))

		with simple.group("control", parent=self.parent.guid):
			core.add_button("control.save", label="save", callback=self.__save, width=90, height=25)
			core.add_same_line()
			core.add_button("control.load", label="load", callback=self.__load, width=90, height=25)

		with simple.node_editor(self.guid, parent=self.parent.guid, link_callback=self.__link, delink_callback=self.__delink):
			...
		self.register("dpgo.nodeLib")

	def __nodelistRefresh(self):
		if "nodelist" in core.get_all_items():
			core.delete_item("nodelist")

		with simple.popup(self.guid, "nodelist", parent="main"):
			for k in self.registryNodes:
				core.add_text(k, default_value=k)
				for obj in self.registry(k):
					name = getattr(obj, '_name', obj.__name__)
					core.add_button(obj.__name__,
						label=name, width=60, height=15,
						callback=self.__nodeAdd, callback_data=obj)

	def __nodeAdd(self, sender, obj):
		core.close_popup("nodelist")
		size = core.get_item_rect_min(sender)
		x = max(0, int(size[0]) - 140)
		y = max(0, int(size[1]) - 40)
		label = getattr(obj, '_name', obj.__class__.__name__)
		print(obj)
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
	def links(self):
		return self.__links.copy()

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

		# full attribute path
		attr1 = core.get_item_children(attr1)[0]
		attr2 = core.get_item_children(attr2)[0]

		data = self.__links.get(left, [])
		data.append(right)
		self.__links[left] = data

		node = right.split('-')[0]
		node = self.__nodes[node]
		node.calculate()

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
