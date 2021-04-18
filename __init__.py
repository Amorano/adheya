"""."""

from dearpygui import core

class Singleton(type):
	"""It has one job to do."""
	_instance = {}
	def __call__(cls, *arg, **kw):
		if cls not in cls._instance:
			cls._instance[cls] = super(Singleton, cls).__call__(*arg, **kw)
		return cls._instance[cls]

class DPGObject(object):
	def __init__(self, name, **kw):
		self.__parent = kw.get('parent', None)

		index = 0
		name = guid = name or self.__class__.__name__
		while name in core.get_all_items():
			index += 1
			name = f"{guid}_{index}"

		self.__guid = name
		self.__prettyname = kw.get('label', name)

	@property
	def parent(self):
		return self.__parent

	@property
	def guid(self):
		return self.__guid

	@property
	def prettyname(self):
		return self.__prettyname
