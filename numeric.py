"""."""

from enum import Enum
from dearpygui import core
from adheya import DPGObject

class ValueType(Enum):
	Integer = 0
	Float = 1

class InputType(Enum):
	Direct = 0
	Drag = 1
	Slider = 2

class Numeric(DPGObject):
	def __init__(self, guid, valueType: ValueType=ValueType.Integer, inputType: InputType=InputType.Direct, **kw):
		super().__init__(guid, **kw)
		kw['parent'] = self.parent.guid

		self.__inputType = inputType
		self.__valueType = valueType
		dfv = kw['default_value'] = kw.get('default_value', 0)

		intype = ['input', 'drag', 'slider'][inputType.value]
		vtype = ['int', 'float'][valueType.value]
		size = len(dfv) if not isinstance(dfv, (int, float)) else ''
		attr = f"add_{intype}_{vtype}{size}"
		self.__cmd = getattr(core, attr)
		self.__cmd(self.guid, **kw)

	@property
	def inputType(self):
		return self.__inputType

	@property
	def valueType(self):
		return self.__valueType
