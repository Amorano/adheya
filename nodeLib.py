"""."""

from dearpygui import core
from adheya.node import DirectionType, Node, AttributeType

class NodeMath(Node):
	def __init__(self, name, **kw):
		super().__init__(name, **kw)
		self.attrAdd('a', AttributeType.Float1, default_value=0.)
		self.attrAdd('b', AttributeType.Float1, default_value=0.)
		self.attrAdd('+', AttributeType.Button, DirectionType.Static, callback=self.__addAttr)
		self.attrAdd('out', AttributeType.Label, DirectionType.Output, default_value=' ')

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

class NodeColor(Node):
	_name = "Colorful"
	_category = "Image"

	def __init__(self, name, **kw):
		super().__init__(name, **kw)
		self.attrAdd('color', AttributeType.Pick4, default_value=(128, 128, 128, 255))

	def calculate(self):
		...

class NodeImage(Node):
	_name = "Image"
	_category = "Image"

	def __init__(self, name, **kw):
		super().__init__(name, **kw)
		self.__file = self.attrAdd('file', AttributeType.FileImage, DirectionType.Output, extensions='.png, .jpg')

	def calculate(self):
		if self.__file is None:
			return
