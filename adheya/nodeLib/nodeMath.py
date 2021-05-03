"""."""

from dearpygui import core
from adheya.feedback import Field
from adheya.general import NumericFloat, Button
from adheya.node import PlugDirection, Node

class NodeMath(Node):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		self.attrAdd('a', NumericFloat, default_value=0.)
		self.attrAdd('b', NumericFloat, default_value=0.)
		self.attrAdd('+', Button, PlugDirection.Static, callback=self.__addAttr)
		self.attrAdd('out', Field, PlugDirection.Output, default_value=' ')

	def __addAttr(self, sender, data):
		print(sender, data)

class NodeAdd(NodeMath):
	_category = "Math"
	_name = "Addition"

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

class NodeSubtract(NodeMath):
	_category = "Math"
	_name = "Subtraction"

class NodeMultiply(NodeMath):
	_category = "Math"
	_name = "Multiply"

class NodeDivide(NodeMath):
	_category = "Math"
	_name = "Division"
