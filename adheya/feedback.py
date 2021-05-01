"""."""

from queue import Queue
from threading import Thread
from dearpygui import core, simple
from adheya import DPGObject
from adheya.layout import Group

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

class ProgressBar(DPGObject):
	_index = 0
	def __init__(self, guid, callback=None, **kw):
		super().__init__(guid)
		self.__idGroup = f"{self.__guid}-group"
		self.__callback = callback
		self.__worker = None
		self.__q = Queue()
		self.__value = 0

		width, _ = self.parent.rect
		kw['width'] = kw.get('width', width)
		kw['show'] = kw.get('show', False)
		kw.pop('parent', None)
		with simple.group(self.__idGroup, width=width, parent=self.guid):
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
