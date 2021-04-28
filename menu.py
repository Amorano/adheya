"""."""

from enum import Enum
from dearpygui import core, simple
from adheya import DPGObject

class MenuEntry(Enum):
	Menu = 0
	Item = 1

class MenuBar(DPGObject):
	def __init__(self, name, **kw):
		super().__init__(name, **kw)
		self.__menu = {}
		kw['parent'] = self.parent.guid
		core.add_menu_bar(self.guid, **kw)
		core.end()

	def add(self, name, **kw):
		m = self.__menu.get(name, None)
		if m is None:
			kw['parent'] = self.guid
			m = Menu(name, **kw)
			self.__menu[name] = m
		else:
			print(f"{name} already exists")
		return m

class Menu(DPGObject):
	def __init__(self, name, parent, **kw):
		kw['parent'] = parent
		super().__init__(name, **kw)
		self.__struct = {}

		with simple.menu(self.guid, **kw):
			...

	def add(self, name, entryType: MenuEntry=MenuEntry.Item, **kw):
		m = self.__struct.get(name, None)
		if m is None:
			kw.pop('parent', None)
			guid = f'{self.guid}-{name}'
			kw['label'] = kw.get('label', name)
			cmd = [Menu, MenuItem][entryType.value]
			m = cmd(guid, self.guid, **kw)
			self.__struct[name] = m
		else:
			print(f"{name} already exists")
		return m

class MenuItem(DPGObject):
	def __init__(self, name, parent, **kw):
		kw['parent'] = parent
		super().__init__(name, **kw)
		core.add_menu_item(name, **kw)
