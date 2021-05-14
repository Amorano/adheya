"""General widgets refer to the core interactive set.

	Widgets that take interactive input like:

	Numeric Entry
	Text Entry
	List, Combo, Radio Array Selection
	File Selection
	Color Picking
"""

import os
from enum import Enum
from dearpygui import core
from adheya import DPGObject
from adheya.layout import Group

class ValueType(Enum):
	Integer = 0
	Float = 1

class InputType(Enum):
	Direct = 0
	Drag = 1
	Slider = 2

# ================ INPUT ================ #

class FileHandle(DPGObject):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)

		self.__data = []
		self.__path = ""
		self.__ext = kw.pop('extensions', '.*')

		cofd = core.open_file_dialog
		g = Group(self.parent, width=32)
		Button(g, label='load', callback=lambda: cofd(self.__load, extensions=self.__ext))

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
	def __init__(self, parent, zoomLevel=0, **kw):
		self.__min = kw.pop('pmin', [0, 0])
		self.__max = kw.pop('pmax', [0, 0])
		super().__init__(parent, **kw)

		self.__idCanvas = f'{self.guid}-canvas'
		core.add_drawing(self.__idCanvas, width=self.__max[0], height=self.__max[1], parent=self.parent.guid)
		self.__data = []
		self.register('zoom', self.__zoom)
		self.__zoom(self, zoomLevel)

	def __zoom(self, sender, level):
		size = pow(2, 5 + level)
		self.__max = (size, size)
		core.configure_item(self.__idCanvas, width=size, height=size)
		self.load()

	def load(self):
		"""Callback when file selector picks new file."""
		if self.path:
			core.draw_image(self.__idCanvas, self.path, pmin=self.__min, pmax=self.__max)

class Numeric(DPGObject):
	def __init__(self, parent, valueType: ValueType=ValueType.Integer, inputType: InputType=InputType.Direct, **kw):
		super().__init__(parent, **kw)
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

class NumericSlider(Numeric):
	def __init__(self, parent, valueType: ValueType=ValueType.Integer, **kw):
		kw.pop('inputType', None)
		super().__init__(parent, valueType, InputType.Slider, **kw)

class NumericDrag(Numeric):
	def __init__(self, parent, valueType: ValueType=ValueType.Integer, **kw):
		kw.pop('inputType', None)
		super().__init__(parent, valueType, InputType.Drag, **kw)

class NumericFloat(Numeric):
	def __init__(self, parent, inputType: InputType=InputType.Direct, **kw):
		kw.pop('valueType', None)
		super().__init__(parent, ValueType.Float, inputType, **kw)

class NumericFloatSlider(Numeric):
	def __init__(self, parent, **kw):
		kw.pop('valueType', None)
		kw.pop('inputType', None)
		super().__init__(parent, ValueType.Float, InputType.Slider, **kw)

class NumericFloatDrag(Numeric):
	def __init__(self, parent, **kw):
		kw.pop('valueType', None)
		kw.pop('inputType', None)
		super().__init__(parent, ValueType.Float, InputType.Drag, **kw)
