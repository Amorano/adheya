"""."""

from time import sleep
from queue import Queue
from threading import Thread
from dearpygui import core
from adheya import DPGObject
from adheya.layout import Group

class Label(DPGObject):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		kw['parent'] = self.parent.guid
		label = kw.pop('label', self.label)
		kw.pop('width', None)
		kw['default_value'] = kw.get('default_value', label)
		core.add_text(self.guid, **kw)

class Field(DPGObject):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		dfv = kw.get('default_value', ' ')
		g = Group(self.parent, horizontal=True)
		self.__label = Label(g.guid, default_value=self.label)
		self.__value = Label(g.guid, default_value=dfv)

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

class ThreadUpdate(Thread):
	"""Thread that updates a set of widgets from a Q."""
	def __init__(self, queue: Queue, callback=None):
		super().__init__()
		self.daemon = True
		self.__q = queue
		self.__callback = callback
		"""Where to yell after the Q is dry."""

	def run(self):
		while self.is_alive:
			# Should be a dict with values to replace
			widgets: dict = self.__q.get()
			if widgets is None:
				break
			for w, v in widgets.items():
				w.value = v
			sleep(0.01)

		if self.__callback:
			self.__callback()

class ThreadProgress(Thread):
	"""Threaded progress bar widget."""
	def __init__(self, progressBar, queue: Queue, callback=None):
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
			self.__progressBar.overlay = overlay
			self.__progressBar.value = val
			sleep(0.01)

		if self.__callback:
			self.__callback()

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
