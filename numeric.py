"""."""

from enum import Enum
from dearpygui import core
from adheya import DPGObject

class ValueType(Enum):
	Integer = 0
	Float = 1

class InputType(Enum):
	Input = 0
	Drag = 1
	Slider = 2

class Numeric(DPGObject):
	def __init__(self, guid, valueType: ValueType=ValueType.Integer, inputType: InputType=InputType.Input, **kw):
		super().__init__(guid, **kw)

		kw['parent'] = self.parent.guid

		self.__inputType = inputType
		self.__valueType = valueType
		self.__value = kw.pop('default_value', 0)

		intype = ['input', 'drag', 'slider'][inputType.value]
		vtype = ['int', 'float'][valueType.value]
		size = len(self.__value)
		attr = f"add_{intype}_{vtype}{size if size > 1 else ''}"
		self.__cmd = getattr(core, attr)
		self.__cmd(self.guid, default_vaule=self.__value, **kw)

	@property
	def inputType(self):
		return self.__inputType

	@property
	def valueType(self):
		return self.__valueType

	@property
	def value(self):
		return self.__value

	@value.setter
	def value(self, value):
		if value == self.__value:
			return
		core.set_value(self.guid, value)
		self.__value = value
