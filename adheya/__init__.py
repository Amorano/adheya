"""."""

from enum import Enum
from dearpygui import core, simple

class Keycode(Enum):
	"""Placeholder for iterator on load to fill."""
	...

_CALL = {}
"""All DPG _callback callbacks pre-loaded."""

class CallbackType(Enum):
	Start = 3
	Exit = 4
	Accelerator = 5
	KeyDown = 6
	KeyPress = 7
	KeyRelease = 8
	MouseClick = 9
	MouseDoubleClick = 10
	MouseDown = 11
	MouseDrag = 12
	MouseMove = 13
	MouseRelease = 14
	MouseWheel = 15
	Resize = 16

	def __str__(self):
		return str(self.name)

class Callback():
	def __init__(self, *arg, **kw):

		self.__event = {k: [] for k in CallbackType}

		core.set_mouse_drag_callback(lambda s, d: self.__callback(s, d, CallbackType.MouseDrag), .1)

		for callType, callback in _CALL.items():
			callback(lambda s, d, c=callType: self.__callback(s, d, c))

	def __callback(self, sender, data, event):
		self.event(sender, event, data)

	def event(self, sender, event, *arg, **kw):
		if callback := self.__event.get(event, None):
			for x in callback:
				x(sender, *arg, **kw)

	def register(self, callback, destination):
		what = self.__event.get(callback, [])
		if destination not in what:
			what.append(destination)
			self.__event[callback] = what

class AdheyaObject():
	"""Main object that does the logics."""
	def __init__(self, *arg, **kw):
		self.__guid = None
		parent = kw.pop('parent', None)
		if parent:
			if not isinstance(parent, str):
				parent = parent.guid
			core.push_container_stack(parent)

		# inject a nice label if none present...
		kw['label'] = kw.get('label', self.__class__.__name__)
		try:
			self.__guid = self._init(*arg, **kw)
		except Exception as e:
			raise Exception(str(e)) from e
		finally:
			if parent:
				core.pop_container_stack()

	def __repr__(self):
		typ = core.get_item_info(self.guid)["type"]
		typ = typ.replace('mvAppItemType::', '')
		return f"{self.__class__.__name__} ({type(self)}) => (<{typ} '{self.__guid}'>)"

	def __str__(self):
		return str(self.__guid)

	def __enter__(self):
		core.push_container_stack(self.__guid)
		return self

	def __exit__(self, *arg, **kw):
		core.pop_container_stack()

	def __getattr__(self, attr):
		return core.get_item_configuration(self.__guid)[attr]

	def __setattr__(self, attr, value):
		try:
			super().__setattr__(attr, value)
		except AttributeError as _:
			core.configure_item(self.__guid, **{attr: value})

	def __del__(self):
		try:
			core.delete_item(self.__guid)
		except Exception as e:
			print(self.__guid)
			print(e)

	def _init(self):
		"""Subclasses call this as the entry point for doing contruction."""
		# they should return the final DPG guid for tracking
		raise Exception("Not Implemented")

	@property
	def guid(self):
		return self.__guid

	@property
	def value(self):
		return core.get_value(self.__guid)

	@property
	def pos(self):
		return (self.x_pos, self.y_pos)

	def moveUp(self):
		core.move_item_up(self.__guid)

	def moveDown(self):
		core.move_item_down(self.__guid)

	def moveItem(self, **kw):
		core.move_item(self.__guid, **kw)

	def set(self, **kw):
		"""Set multiple attributes at once."""
		core.configure_item(self.__guid, **kw)

	def clean(self):
		"""Remove only any and all children."""
		core.delete_item(self.__guid, children_only=True)

class DPGO(AdheyaObject):
	"""Special factory wrap for DPG core.add_* commands."""

	_cmd = ValueError

	def _init(self, *arg, **kw):
		"""Pass thru the DPG command with arguments."""
		return self._cmd(*arg, **kw)

def _initialize_():
	_badnames = {
		'NodeAttr': 'NodeAttribute',
		'CheckBox': 'Checkbox'
	}
	_objectMap = {}
	enum = []

	# kind of a cheat since the build commands are all alphabetical via add_*
	for cmd in dir(core):
		if cmd.startswith('add_'):
			name = cmd.replace('add_', '')
			name = ''.join([r.title() for r in name.split('_')])
			_objectMap[name] = {
				'_cmd': getattr(core, cmd)
			}

		if cmd.startswith('mvKey_'):
			name = ''.join(cmd.split('_')[1:])
			val = getattr(core, cmd)
			enum.append((name, val))

		if cmd.startswith('mvTheme'):
			part = cmd.replace('mvTheme', '').split('_')
			ctrl = part[1]
			# replace the current inconsistant names
			if ctrl in _badnames:
				ctrl = _badnames[ctrl]
			name = part[1] if ctrl == '' else '_'.join(part[2:])

			data = _objectMap[ctrl]
			prefix = 'color' if part[0] == 'Col' else 'style'
			data[f"_{prefix}{name}"] = getattr(core, cmd)
			_objectMap[ctrl] = data

		elif cmd.endswith('_callback'):
			callback = ''.join(t.title() for t in cmd.split('_')[1:-1])
			_CALL[CallbackType[callback]] = cmd

	# rewire the gather'd values for Keycodes
	globals()['Keycode'] = Enum('Keycode', enum)

	for cmd, data in _objectMap.items():
		# create DPGO subclass with cmd as metadata for future factory
		globals()[cmd] = type(cmd, (DPGO, ), data)

_initialize_()

def register(cls):
	"""Decorator to override a core type with a custom version.

	If you want to extend objects, you should inherit and override _init_ and
	provide your own styling.

	The core types are meant as a base for all creation calls, purely to be able
	to transact the DPG API 1:1.
	"""
	name = cls.__name__
	if (globals().get(name, None)) is None:
		raise Exception(f"registering override for non-existant type {name}")

	# establish the new class pointer
	globals()[cls.__name__] = cls

# now import the custom overrides
import adheya.menu # as __widget__menu
#import adheya.menu as __widget__menu
#import adheya.menu as __widget__menu
#import adheya.menu as __widget__menu
