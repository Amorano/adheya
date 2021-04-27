"""."""

from __future__ import annotations
from enum import Enum
from typing import Union
from dearpygui import core

class CallbackType(Enum):
	Render = 0
	Resize = 1
	MouseDown = 2
	MouseDrag = 3
	MouseMove = 4
	MouseDoubleClick = 5
	MouseClick = 6
	MouseRelease = 7
	MouseWheel = 8
	KeyDown = 9
	KeyPress = 10
	KeyRelease = 11
	Accelerator = 12

class Singleton(type):
	"""It has one job to do."""
	_instance = {}
	def __call__(cls, *arg, **kw):
		if cls not in cls._instance:
			cls._instance[cls] = super(Singleton, cls).__call__(*arg, **kw)
		return cls._instance[cls]

class Callbacks(metaclass=Singleton):
	def __init__(self, *arg, **kw):
		self.__event = {k: [] for k in CallbackType}

		core.set_render_callback(lambda s, d: self.__callback(s, d, CallbackType.Render))
		core.set_resize_callback(lambda s, d: self.__callback(s, d, CallbackType.Resize))
		core.set_mouse_down_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseDown))
		core.set_mouse_drag_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseDrag), 10)
		core.set_mouse_move_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseMove))
		core.set_mouse_double_click_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseDoubleClick))
		core.set_mouse_click_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseClick))
		core.set_mouse_release_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseRelease))
		core.set_mouse_wheel_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseWheel))
		core.set_key_down_callback(lambda s, d: self.__callback(s, d, CallbackType.KeyDown))
		core.set_key_press_callback(lambda s, d: self.__callback(s, d, CallbackType.KeyPress))
		core.set_key_release_callback(lambda s, d: self.__callback(s, d, CallbackType.KeyRelease))
		core.set_accelerator_callback(lambda s, d: self.__callback(s, d, CallbackType.Accelerator))

	def __callback(self, sender, data, event):
		for cmd in self.__event[event]:
			cmd(sender, data)

	def register(self, callback: Union[CallbackType, str], destination):
		what = self.__event.get(callback, [])
		if destination not in what:
			what.append(destination)
			self.__event[callback] = what

	def event(self, sender, event, *arg, **kw):
		callback = self.__event.get(event, [])
		for x in callback:
			x(*arg, **kw)

class DPGObject(object):
	# everything made in this "wrapper" tracked via guid
	_REGISTRY = {}
	_CALLBACK = Callbacks()

	def __init__(self, guid, **kw):
		# horrible mechanism to map DPG objects with no native python side wrapper
		parent = kw.get('parent', None)
		if isinstance(parent, str):
			parent = self._REGISTRY.get(parent, parent)
			if isinstance(parent, str):
				parent = self._REGISTRY[parent] = DPGObject(parent) #, unique=False)

		# for uniqueness across all widgets; just because.
		index = 0
		name = guid = guid or self.__class__.__name__
		# could be a non-wrapped item
		items = core.get_all_items()
		while guid in items:
			index += 1
			guid = f"{name}_{index}"

		self.__parent = parent
		self.__label = kw.get('label', guid)
		self.__guid = guid
		self._REGISTRY[guid] = self

	def __repr__(self):
		return self.__label

	def __getattr__(self, attr):
		try:
			return getattr(self.parent, attr)
		except AttributeError as _:
			return core.get_item_configuration(self.__guid)[attr]

	def __setattr__(self, attr, value):
		if attr.startswith('_'):
			super().__setattr__(attr, value)
		else:
			core.configure_item(self.__guid, **{attr: value})

	@property
	def parent(self) -> DPGObject:
		return self.__parent

	@property
	def guid(self) -> str:
		return self.__guid

	@property
	def label(self) -> str:
		return self.__label

	@property
	def hierarchy(self):
		def scan(widget, level=0):
			ret = ''
			if isinstance(widget, list):
				for item in widget:
					ret += scan(item, level + 1)
			else:
				ret += f"{'  ' * level}| {widget}\n"
			return ret

		children = self.children()
		return f'{self}\n' + scan(children)

	def register(self, callback: Union[CallbackType, str], destination):
		self._CALLBACK.register(callback, destination)

	def event(self, event, *arg, **kw):
		self._CALLBACK.event(self, event, *arg, **kw)

	def children(self, recurse=True, flat=False):
		ret = [v for v in self._REGISTRY.values() if v.parent == self]
		if recurse:
			for k in ret:
				if isinstance(k, list):
					continue
				children = k.children(recurse=recurse)
				if len(children) == 0:
					continue
				if not flat:
					children = [children]
				ret.extend(children)
		return ret
