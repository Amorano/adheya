"""."""

from enum import Enum
from dearpygui import core, simple
from adheya import DPGObject, CallbackType
from adheya.general import Label, FileHandle, FileImage, Numeric, InputType

class PlugType(Enum):
	Input = 0
	Output = 1
	Static = 2

	@staticmethod
	def filter(node):
		config = core.get_item_configuration(node)
		if config.get('output', None):
			return PlugType.Output
		if config.get('static', None):
			return PlugType.Static
		return PlugType.Input

class AttributeType(Enum):
	Bool = 0
	Int1 = 1
	Int2 = 2
	Int3 = 3
	Int4 = 4
	Float1 = 5
	Float2 = 6
	Float3 = 7
	Float4 = 8
	Color3 = 9
	Color4 = 10
	Pick3 = 11
	Pick4 = 12
	String = 13
	Button = 14
	Label = 15
	FileHandle = 16
	FileImage = 17

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
		kw['parent'] = parent
		super().__init__(plug, **kw)
		self.__type = attrType
		self.__attr = attr
		self.__plugType = plugType

		output = plugType == PlugType.Output
		static = plugType == PlugType.Static

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

		with simple.node(self.guid, **kw):
			...

	def event(self, event, *arg, **kw):
		"""Cast the event to all the attributes."""
		for callback in (self.__attrInput, self.__attrStatic, self.__attrOutput):
			for cb in callback.values():
				cb.event(event, *arg, **kw)

	def calculate(self):
		"""Propigates the value based on depth first."""
		return True

	def attrAdd(self, guid, attrType: AttributeType, plugType: PlugType=PlugType.Input, **kw) -> NodeAttribute:
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
		kw.pop('parent', None)
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
	def dump(self):
		for i in self.__attrInput:
			print(i)

class NodeZoom(Node):
	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		self.__idGroup = f"{self.guid}-group"
		with simple.group(self.__idGroup, parent=self.guid):
			...

		self.__slider = Numeric(f"{self.guid}-zoom", label='', parent=self.__idGroup, width=1,
			inputType=InputType.Slider, default_value=1, min_value=0, max_value=3, clamped=True,
			callback=lambda s, d: self.__zoom())

		self.register(CallbackType.Resize, self.__resize)
		self.__resize(self, None)

	def __resize(self, sender, data):
		w, _ = self.parent.size
		w = int(min(max(w, 16), 256))
		core.configure_item(self.__idGroup, width=w)

	def __zoom(self):
		self.event('zoom', self.__slider.value)

	@property
	def zoomLevel(self):
		return self.__slider.value
