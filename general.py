"""."""

import os
from dearpygui import core, simple
from adheya import DPGObject

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
		self.__max = kw.pop('pmax', [0, 0])
		super().__init__(guid, **kw)
		self.__idCanvas = f'{self.guid}-canvas'
		core.add_drawing(self.__idCanvas, width=self.__max[0], height=self.__max[1], parent=self.parent.guid)
		self.__data = []
		self.register('zoom', self.__zoom)
		zoom = self.parent.zoomLevel
		self.__zoom(zoom)

	def __zoom(self, level):
		size = pow(2, 5 + level)
		self.__max = (size, size)
		core.configure_item(self.__idCanvas, width=size, height=size)
		self.load()

	def load(self):
		"""Callback when file selector picks new file."""
		if self.path:
			core.draw_image(self.__idCanvas, self.path, pmin=self.__min, pmax=self.__max)
