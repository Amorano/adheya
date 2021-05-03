"""."""

from adheya.general import ColorPicker, FileImage
from adheya.node import PlugDirection, Node, NodeZoom

class NodeColor(Node):
	_name = "Color4"
	_category = "Image"

	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		self.attrAdd('color', ColorPicker, PlugDirection.Output, default_value=(128, 128, 128, 255))

class NodeImage(NodeZoom):
	_name = "Image"
	_category = "Image"

	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		self.__file = self.attrAdd('file', FileImage, PlugDirection.Output, extensions='.png, .jpg')

	def calculate(self):
		if self.__file is None:
			return

class NodeBlend(Node):
	_name = "Blend"
	_category = "Image"

	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		self.attrAdd('color', ColorPicker, PlugDirection.Output, default_value=(128, 128, 128, 255))
