"""."""

from queue import Queue
from threading import Thread
from dearpygui import core
from adheya import DPGObject
from adheya.layout import Group
from adheya.general import Text

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

class Label(DPGObject):
	_CMD = core.add_text

class Field(DPGObject):
	def __init__(self, parent, *arg, **kw):
		super().__init__(parent, *arg, **kw)
		dfv = kw.get('default_value', ' ')
		g = Group(self.parent, horizontal=True)
		self.__label = Text(g.guid, default_value=self.label)
		self.__value = Text(g.guid, default_value=dfv)

	@property
	def text(self):
		return self.__label.value

	@text.setter
	def text(self, val):
		self.__label = val

	@property
	def value(self):
		return self.__value.value

	@value.setter
	def value(self, val):
		self.__value = val

class ProgressBar(DPGObject):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)

		self.__callback = kw.pop('callback', None)
		self.__worker = None
		self.__q = Queue()

		width, _ = self.parent.rect
		kw['width'] = kw.get('width', width)
		kw['show'] = kw.get('show', False)
		kw.pop('parent', None)

		self.__group = Group(self, width=width)
		core.add_progress_bar(self.__group, **kw)

	@property
	def value(self):
		return self.value

	@value.setter
	def value(self, val):
		# self.value = val
		data = f'{round(val * 100)}%'
		if val < 0:
			val = 0
		if val > 1.:
			val = None
		self.__q.put((val, data))

	def start(self):
		self.show = True
		# simple.show_item(self.__guid)
		self.__worker = ThreadProgress(self, self.__q, callback=lambda: self.__callback(self.__guid))
		self.__worker.start()
