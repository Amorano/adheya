"""."""

from dearpygui import core
from adheya.node import PlugType, AttributeType, Node

class NodeMath(Node):
	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		self.attrAdd('a', AttributeType.Float1, default_value=0.)
		self.attrAdd('b', AttributeType.Float1, default_value=0.)
		self.attrAdd('+', AttributeType.Button, PlugType.Static, callback=self.__addAttr)
		self.attrAdd('out', AttributeType.Label, PlugType.Output, default_value=' ')

	def __addAttr(self, sender, data):
		print(sender, data)

class NodeAdd(NodeMath):
	_name = "Addition"
	_category = "Math"

	def calculate(self):
		# specific to this node first....
		value = 0
		for x in self.inputs:
			value += core.get_value(x)

		# set local first
		for x in self.outputs:
			core.set_value(x, value)

		# now tell the manager to propigate
		super().calculate()
