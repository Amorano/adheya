"""."""

from dearpygui import core

# everything made in this "wrapper" tracked via guid
_REGISTRY = {}

class Singleton(type):
	"""It has one job to do."""
	_instance = {}
	def __call__(cls, *arg, **kw):
		if cls not in cls._instance:
			cls._instance[cls] = super(Singleton, cls).__call__(*arg, **kw)
		return cls._instance[cls]

class DPGObject(object):
	def __init__(self, name, **kw):
		index = 0
		name = guid = name or self.__class__.__name__
		while name in core.get_all_items():
			index += 1
			name = f"{guid}_{index}"

		global _REGISTRY
		parent = kw.get('parent', None)
		if isinstance(parent, str):
			parent = _REGISTRY[parent]

		self.__parent = parent
		self.__guid = name
		self.__prettyname = kw.get('label', name)
		_REGISTRY[name] = self

	@property
	def parent(self):
		return self.__parent

	@property
	def guid(self):
		return self.__guid

	@property
	def prettyname(self):
		return self.__prettyname

	def __getattr__(self, attr):
		return core.get_item_configuration(self.guid)[attr]
