"""."""

import os
from enum import Enum
from queue import Queue
from threading import Thread
from dearpygui import core, simple
from adheya import DPGObject, DPGWrap

class ValueType(Enum):
	Integer = 0
	Float = 1

class InputType(Enum):
	Direct = 0
	Drag = 1
	Slider = 2

class Container(DPGObject):
	def __enter__(self):
		yield self

	def __exit__(self, *arg):
		... #core.end()

@DPGWrap(core.add_group)
class Group(Container):
	...

class Label(DPGObject):
	def __init__(self, guid, **kw):
		super().__init__(guid, **kw)
		dfv = kw.get('default_value', ' ')
		group = f'{self.guid}-group'
		with Group(group, parent=self.parent.guid, horizontal=True):
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
	def __init__(self, guid, zoomLevel=0, **kw):
		self.__min = kw.pop('pmin', [0, 0])
		self.__max = kw.pop('pmax', [0, 0])
		super().__init__(guid, **kw)
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

class ThreadProgress(Thread):
	"""Threaded progress bar widget."""
	def __init__(self, progressBar, queue, callback=None):
		super().__init__()
		self.daemon = True
		self.__q = queue
		self.__progressBar = progressBar
		self.__callback = callback

	def run(self):
		while self.is_alive:
			val, overlay = self.__q.get()
			if val is None:
				break
			core.configure_item(self.__progressBar.guid, overlay=overlay)
			core.set_value(self.__progressBar.guid, val)

		if self.__callback:
			self.__callback()

class ProgressBar():
	_index = 0
	def __init__(self, parent, guid=None, callback=None, **kw):

		guid = guid or self.__class__.__name__
		self.__guid = f'{parent}-{guid}.{ProgressBar._index}'
		self.__idGroup = f"{self.__guid}-group"
		ProgressBar._index += 1

		self.__callback = callback
		self.__worker = None
		self.__q = Queue()
		self.__value = 0

		width, _ = core.get_item_rect_size(parent)
		width = int(width)
		kw['width'] = kw.get('width', width)
		kw['show'] = kw.get('show', False)
		kw.pop('parent', None)
		with simple.group(self.__idGroup, width=width, parent=parent):
			core.add_progress_bar(self.__guid, **kw)

	@property
	def progress(self):
		return self.__value

	@progress.setter
	def progress(self, val):
		self.__value = val
		data = f'{round(val * 100)}%'
		if val < 0:
			val = 0
		if val > 1.:
			val = None
		self.__q.put((val, data))

	@property
	def guid(self):
		return self.__guid

	def start(self):
		self.show = True
		# simple.show_item(self.__guid)
		self.__worker = ThreadProgress(self, self.__q, callback=lambda: self.__callback(self.__guid))
		self.__worker.start()

	def reset(self):
		self.__value = 0

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
