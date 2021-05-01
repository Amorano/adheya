"""."""

from adheya.node import PlugType, AttributeType, Node, NodeZoom

class NodeColor(Node):
	_name = "Color4"
	_category = "Image"

	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		self.attrAdd('color', AttributeType.Pick4, PlugType.Output, default_value=(128, 128, 128, 255))

	def calculate(self):
		...

class NodeImage(NodeZoom):
	_name = "Image"
	_category = "Image"

	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		self.__file = self.attrAdd('file', AttributeType.FileImage, PlugType.Output, extensions='.png, .jpg')

	def calculate(self):
		if self.__file is None:
			return

class NodeBlend(Node):
	_name = "Blend"
	_category = "Image"

	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		self.attrAdd('color', AttributeType.Pick4, PlugType.Output, default_value=(128, 128, 128, 255))

	def calculate(self):
		...
