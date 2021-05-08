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

	def __str__(self):
		return str(self.name)

class Callback():
	def __init__(self, *arg, **kw):
		self.__event = {k: [] for k in CallbackType}

		core.set_mouse_drag_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseDrag), .1)
		core.set_render_callback(lambda s, d: self.__callback(s, d, CallbackType.Render))
		core.set_resize_callback(lambda s, d: self.__callback(s, d, CallbackType.Resize))
		core.set_mouse_down_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseDown))
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
		self.event(sender, event, data)

	def event(self, sender, event, *arg, **kw):
		callback = self.__event.get(event, None)
		if callback:
			# find the "string" sender in the local registry
			sender = Registry[sender]
			if sender is None:
				sender = DPGObject(None, name=sender)
			for x in callback:
				x(sender, *arg, **kw)

	def register(self, callback: Union[CallbackType, str], destination):
		what = self.__event.get(callback, [])
		if destination not in what:
			what.append(destination)
			self.__event[callback] = what

Callback = Callback()

class Registry(object):
	"""Where all DPG objects are tracked."""
	def __init__(self, *arg, **kw):
		super().__init__(*arg, **kw)
		self.__registry = {}
		self.__mainWindow = None

	def __contains__(self, val):
		return val in self.__registry

	def __getitem__(self, key):
		return self.__registry.get(key, None)

	def __setitem__(self, guid, obj):
		# must exist inside the DPG space if we are tracking
		#if guid not in core.get_all_items():
		#	core.log_error(f"{guid} not in DPG database.")
		#	return
		if guid in core.get_all_items() and core.get_item_type(guid) == 'mvAppItemType::Window':
			if self.__mainWindow:
				raise Exception("only allowed one main window per dpg instance")
			self.__mainWindow = obj
			print('main window set')
		self.__registry[guid] = obj
		return obj

	def __delitem__(self, guid: str):
		if core.does_item_exist(guid):
			for child in core.get_item_children(guid) or []:
				del Registry[child]
			core.delete_item(guid)
		return self.__registry.pop(guid, None)

	@property
	def keys(self):
		return list(self.__registry.keys())

	@property
	def main(self):
		return self.__mainWindow

	def find(self, guid):
		"""Search DPG for the item."""
		# assume only str or DPGObject
		if not isinstance(guid, str):
			return guid
		# anything local first?
		if p := self.__registry.get(guid, None):
			return p
		# check the DPG registry, and create a wrap if missing
		if core.does_item_exist(guid):
			parent = core.get_item_configuration(guid).get('parent', None)
			return DPGObject(parent, guid=guid)

Registry = Registry()

class DPGObject(object):
	# the DPG routed command, if any
	_CMD = None
	# if this widget needs to pass its guid to the DPG constructor
	_GUID = True

	def __init__(self, parent, *arg, guid=None, **kw):
		# register any parent that might not be, and fixate mine, or use Main Window if any
		parent = Registry.find(Registry.main or parent)
		name = guid = guid or self.__class__.__name__

		# could be an existing named item
		index = 0
		while guid in Registry:
			guid = f"{name}_{index}"
			index += 1

		self.__guid = guid
		self.__label = kw.get('label', guid)
		self.__parent = parent
		if self._CMD:
			# its just a pass thru widget, so pass it thru
			kw['parent'] = parent.guid if parent else None
			if self._GUID:
				self._CMD(guid, **kw)
			else:
				self._CMD(**kw)

		Registry[guid] = self
		if Registry[guid] is None:
			raise Exception("COMPLETE FAILURE")

	def __str__(self):
		return self.__guid

	def __getattr__(self, attr):
		try:
			return getattr(self.__parent, attr)
		except AttributeError as _:
			try:
				return core.get_item_configuration(self.__guid)[attr]
			except Exception as _:
				ret = f"missing {self.__guid}.{attr}"
				core.log_error(ret)

	def __setattr__(self, attr, value):
		if attr.startswith('_'):
			super().__setattr__(attr, value)
		else:
			core.configure_item(self.__guid, **{attr: value})

	def delete(self):
		del Registry[self.__guid]

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

	@property
	def value(self):
		return core.get_value(self.__guid)

	@value.setter
	def value(self, value):
		core.set_value(self.__guid, value)

	@property
	def size(self):
		w, h = core.get_item_rect_size(self.__guid)
		return int(w), int(h)

	@property
	def dpgType(self):
		return core.get_item_type(self.__guid)

	def configure(self, **kw):
		core.configure_item(self.__guid, **kw)

	def children(self, recurse=True, flat=False):
		ret = [v for v in self._REGISTRY.values() if v.parent == self]
		if not recurse:
			return ret
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

	def register(self, callback: Union[CallbackType, str], destination):
		Callback.register(callback, destination)

	def event(self, event, *arg, **kw):
		Callback.event(self, event, *arg, **kw)
