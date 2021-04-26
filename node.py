"""."""

import os
from enum import Enum
from dearpygui import core, simple
from adheya import DPGObject

class DirectionType(Enum):
	Input = 0
	Output = 1
	Static = 2

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
	Color3 = 10
	Color4 = 11
	Pick3 = 12
	Pick4 = 13
	String = 14
	Button = 15
	Label = 16
	FileHandle = 17
	FileImage = 18

class Label(DPGObject):
	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		dfv = kw.get('default_value', ' ')
		group = f'{self.guid}-group'
		with simple.group(group, parent=self.parent.guid, horizontal=True):
			core.add_text(f'{group}.label', default_value=self.label)
			core.add_text(f'{group}.text', default_value=dfv)

	@property
	def text(self):
		return core.get_value(f'{self.guid}-group.label')

	@text.setter
	def text(self, val):
		core.set_value(f'{self.guid}-group.label', val)

	@property
	def value(self):
		return core.get_value(f'{self.guid}-group.text')

	@value.setter
	def value(self, val):
		core.set_value(f'{self.guid}-group.text', val)

class FileHandle(DPGObject):
	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)

		self.__data = []
		self.__path = ""
		self.__ext = kw.pop('extensions', '.*')

		self.__idGroup = f'{self.guid}-group'
		self.__idPicker = f'{self.guid}-picker'

		cofd = core.open_file_dialog
		with simple.group(self.__idGroup, width=32):
			core.add_button(self.__idPicker, label='load', callback=lambda: cofd(self.__load, extensions=self.__ext))

	@property
	def group(self):
		return self.__idGroup

	@property
	def picker(self):
		return self.__idPicker

	@property
	def path(self):
		"""Current path picked."""
		return self.__path

	def __load(self, sender, data):
		path = os.sep.join(data)
		if self.__path == path:
			return
		if os.path.exists(path):
			self.__path = path

		# callback
		self.load()

	def load(self):
		"""Override in children classes."""
		...

class FileImage(FileHandle):
	def __init__(self, guid, **kw):
		self.__min = kw.pop('pmin', [0, 0])
		self.__max = kw.pop('pmax', [64, 64])
		super().__init__(guid, **kw)
		self.__idCanvas = f'{self.guid}-canvas'
		core.add_drawing(self.__idCanvas, width=self.__max[0], height=self.__max[1], parent=self.parent.guid)
		self.__data = []
		self.callback('zoom', self.__zoom)

	def __zoom(self, level):
		size = pow(2, 5 + level)
		self.__max = (size, size)
		core.configure_item(self.__idCanvas, width=size, height=size)
		self.load()

	def load(self):
		"""Callback when file selector picks new file."""
		if self.path:
			core.draw_image(self.__idCanvas, self.path, pmin=self.__min, pmax=self.__max)

class NodeAttribute(DPGObject):
	_ATTRMAP = {
		AttributeType.Bool: core.add_checkbox,
		AttributeType.Int1: core.add_input_int,
		AttributeType.Int2: core.add_input_int2,
		AttributeType.Int3: core.add_input_int3,
		AttributeType.Int4: core.add_input_int4,
		AttributeType.Float1: core.add_input_float,
		AttributeType.Float2: core.add_input_float2,
		AttributeType.Float3: core.add_input_float3,
		AttributeType.Float4: core.add_input_float4,
		AttributeType.Color3: core.add_color_edit3,
		AttributeType.Color4: core.add_color_edit4,
		AttributeType.Pick3: core.add_color_picker3,
		AttributeType.Pick4: core.add_color_picker4,
		AttributeType.String: core.add_input_text,
		AttributeType.Button: core.add_button,
		AttributeType.Label: Label,
		AttributeType.FileHandle: FileHandle,
		AttributeType.FileImage: FileImage
	}

	def __init__(self, parent, plug, plugType, attr, attrType, **kw):
		super().__init__(plug, **kw)
		self.__type = attrType
		self.__attr = attr
		self.__plugType = plugType
		output = plugType == DirectionType.Output
		static = plugType == DirectionType.Static

		with simple.node_attribute(plug, parent=parent, output=output, static=static):
			# mapped command to create plug inside this attribute wrapper
			kw['parent'] = self.guid
			kw['width'] = kw.get('width', 80)
			self.__widget = self._ATTRMAP[attrType](attr, **kw)

	@property
	def attrType(self):
		return self.__type

	@property
	def attr(self):
		return self.__attr

	@property
	def plugType(self):
		return self.__plugType

	def event(self, event, *arg, **kw):
		if self.__widget:
			self.__widget.event(event, *arg, **kw)

class Node(DPGObject):
	def __init__(self, guid, **kw):
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
		super().__init__(guid, **kw)

		self.__attrInput = {}
		self.__attrOutput = {}
		self.__attrStatic = {}

		self.__zoomLevel = 0
		self.__zoomExtent = (0, 3)

		idGroup = f"{self.guid}-group"
		self.__idZoom = f"{idGroup}-zoom"
		with simple.node(self.guid, **kw):
			width = simple.get_item_width(self.guid)
			with simple.node_attribute(f"{self.guid}-attr", static=True):
				with simple.group(idGroup, horizontal=True, width=width):
					core.add_button(f"{idGroup}-zin", label='-', callback=self.__zoom, callback_data=-1, width=20)
					core.add_text(self.__idZoom, default_value=str(self.__zoomLevel))
					core.add_button(f"{idGroup}-zout", label='+', callback=self.__zoom, callback_data=1, width=20)

	def __zoom(self, sender, data):
		old = self.__zoomLevel
		self.__zoomLevel += int(data)
		self.__zoomLevel = min(self.__zoomExtent[1], max(self.__zoomExtent[0], self.__zoomLevel))
		if self.__zoomLevel != old:
			core.set_value(self.__idZoom, str(self.__zoomLevel))
			self.__event('zoom', self.__zoomLevel)

	def __event(self, event, *arg, **kw):
		"""Cast the event to all the attributes."""
		for callback in (self.__attrInput, self.__attrStatic, self.__attrOutput):
			for cb in callback.values():
				cb.event(event, *arg, **kw)

	def calculate(self):
		"""Propigates the value based on depth first."""
		return True

	def attrAdd(self, guid, attrType: AttributeType, plugType: DirectionType=DirectionType.Input, **kw) -> NodeAttribute:
		if guid in self.__attrOutput or guid in self.__attrInput or guid in self.__attrStatic:
			raise Exception(f"Attribute {guid} already exists")

		attr = [self.__attrInput, self.__attrOutput, self.__attrStatic][plugType.value]

		# the outside wrapper and thing which DPG connects
		plugname = f"{self.guid}-{guid}"

		# the actual attribute where the value is held
		attrname = f"{plugname}.attr"
		kw['label'] = kw.get('label', guid)
		kw.pop('static', None)
		kw.pop('output', None)
		na = NodeAttribute(self.guid, plugname, plugType, attrname, attrType, **kw)
		attr[attrname] = na
		return na

	@property
	def outputs(self):
		return self.__attrOut.copy()

	@property
	def inputs(self):
		return self.__attrInput.copy()

	@property
	def zoomLevel(self):
		return self.__zoomLevel
