"""."""

from dearpygui import core
import adheya as aha

@aha.register
class MenuBar(aha.MenuBar):
	def __init__(self, *arg, **kw):
		self.__menu = {}
		super().__init__(*arg, **kw)

	def add(self, name, **kw):
		m = self.__menu.get(name, None)
		if m is None:
			m = aha.Menu(**kw)
			self.__menu[name] = m
		else:
			core.log_error(f"{name} already exists")
		return m

	def __getitem__(self, item):
		return self.__menu[item]

@aha.register
class Menu(aha.Menu):
	def __init__(self, *arg, **kw):
		self.__struct = {}
		super().__init__(*arg, **kw)

	def __add(self, name, cmd, **kw):
		m = self.__struct.get(name, None)
		if m is None:
			kw['parent'] = self.guid
			m = cmd(**kw)
			self.__struct[name] = m
		else:
			core.log_error(f"{name} already exists")
		return m

	def addItem(self, name, **kw):
		return self.__add(name, aha.MenuItem, **kw)

	def addMenu(self, name, **kw):
		return self.__add(name, aha.Menu, **kw)

@aha.register
class Button(aha.Button):
	"""Adheya version of a DPG Button++."""
	def _init(self, *arg, **kw):
		# to finalize you must return the managing DPG guid
		guid = aha.Button(*arg, **kw)
		return guid

@aha.register
class Window(aha.Window):
	"""Adheya custom default version for a DPG window."""

	_MAIN = None

	def __init__(self, *arg, **kw):
		self.__mainbar = None
		super().__init__(*arg, **kw)

	def _init(self, *arg, **kw):
		guid = core.add_window(*arg, **kw)
		self.__mainbar = aha.MenuBar(parent=guid)
		return guid

	@property
	def mainbar(self):
		return self.__mainbar

	def open(self):
		if aha.Window._MAIN:
			self.show = True
			return
		aha.Window._MAIN = self.guid
		vp = core.create_viewport()
		core.setup_dearpygui(viewport=vp)
		core.show_viewport(vp)
		while core.is_dearpygui_running():
			core.render_dearpygui_frame()
		core.cleanup_dearpygui()
