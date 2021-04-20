"""."""

from dearpygui import core
from .node import Node, AttributeType

class NodeMath(Node):
	def __init__(self, name, **kw):
		super().__init__(name, **kw)
		self.attrAddIn('a', AttributeType.Float1, default_value=0.)
		self.attrAddIn('b', AttributeType.Float1, default_value=0.)
		self.attrAddOut('out', AttributeType.Label, default_value=' ')

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

class NodeColor(Node):
	_name = "Colorful"
	_category = "Image"

	def calculate(self):
		val = core.get_value(self._a) + core.get_value(self._b)
		core.set_value(self._out, val)

class NodeImage(Node):
	_name = "Image"
	_category = "Image"

	def calculate(self):
		val = core.get_value(self._a) + core.get_value(self._b)
		core.set_value(self._out, val)
