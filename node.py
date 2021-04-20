"""."""

from enum import Enum
from dearpygui import core, simple
from adheya import DPGObject

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
		dfv = kw.get('default_value', ' ')
		with simple.group(f'{self.guid}-group', parent=self.parent.guid):
			core.add_text(f'{self.guid}-label', default_value=self.label)
			core.add_same_line()
			core.add_text(f'{self.guid}-text', default_value=dfv)

	@property
	def text(self):
		return core.get_value(f'{self.guid}-label')

	@text.setter
	def text(self, val):
		core.set_value(f'{self.guid}-label', val)

	@property
	def value(self):
		return core.get_value(f'{self.guid}-text')

	@value.setter
	def value(self, val):
		core.set_value(f'{self.guid}-text', val)

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
		AttributeType.String: core.add_input_text,
		AttributeType.Label: Label
	}

	def __init__(self, parent, plug, attrType, attr, output=False, **kw):
		super().__init__(plug, **kw)
		kw['width'] = kw.get('width', 80)
		self.__type = attrType
		self.__attr = attr
		self.__output = output

		with simple.node_attribute(plug, parent=parent, output=output):
			# mapped command to create plug inside this attribute wrapper
			kw['parent'] = self.guid
			self._ATTRMAP[attrType](attr, **kw)

	@property
	def typ(self):
		return self.__type

	@property
	def attr(self):
		return self.__attr

	@property
	def output(self):
		return self.__output

class Node(DPGObject):
	def __init__(self, name, **kw):
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
		super().__init__(name, **kw)

		self.__attrInput = {}
		self.__attrOutput = {}

		with simple.node(self.guid, **kw):
			...

	def calculate(self):
		"""Propigates the value based on depth first."""
		return True

	def __attrHelper(self, name, attrType: AttributeType, output=False, **kw):
		if name in self.__attrOutput or name in self.__attrInput:
			raise Exception(f"Attribute {name} already exists")

		attr = self.__attrOutput if output else self.__attrInput

		# the outside wrapper and thing which DPG connects
		plugname = f"{self.guid}-{name}"

		# the actual attribute where the value is held
		attrname = f"{plugname}.attr"
		kw['label'] = kw.get('label', name)

		na = NodeAttribute(self.guid, plugname, attrType, attrname, output=output, **kw)
		attr[attrname] = na

	def attrAddOut(self, name, attrType: AttributeType, **kw):
		self.__attrHelper(name, attrType, output=True, **kw)

	def attrAddIn(self, name, attrType: AttributeType, **kw):
		self.__attrHelper(name, attrType, **kw)

	@property
	def outputs(self):
		return self.__attrOut.copy()

	@property
	def inputs(self):
		return self.__attrInput.copy()
