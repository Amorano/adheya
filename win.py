"""."""

import re
from dearpygui import core, simple
from adheya.menu import MenuBar
from adheya.theme import ThemeManager
from adheya import DPGObject, Singleton

class Window(DPGObject):
	def __init__(self, name=None, **config):
		super().__init__(name, **config)
		with simple.window(self.guid, **config):
			self.__menubar = MenuBar(None, parent=self) if config['menubar'] else None

	@property
	def menubar(self):
		return self.__menubar

class WindowMain(Window, metaclass=Singleton):
	def __init__(self, name=None, **config):
		config['menubar'] = config.get('menubar', True)
		super().__init__(name, **config)

		self.__cache = {}

		# close event as well -- can register for "close"/"exit"
		core.set_exit_callback(self.__exit)

		self.__theme = ThemeManager(theme="Jovian_Grey")
		self.__cacheRefresh()

	def __cacheRefresh(self):
		"""Retreive the DearPyGui item stack and categorize them according to type.

		Cache initial interface, provide thin layer to track "new" controls or
		the removal of existing controls.

		Allows the cache to be in sync with the present UI state.
		"""
		self.__cache = {}
		for item in core.get_all_items():
			typ = core.get_item_type(item).replace('mvAppItemType::', '').lower()
			data = self.__cache.get(typ, [])
			data.append(item)
			self.__cache[typ] = data

	def __exit(self, sender, data):
		core.stop_dearpygui()

	@property
	def cache(self):
		return self.__cache

	def open(self):
		core.start_dearpygui(primary_window=self.guid)

	def filter(self, typ=None, ignoreBuiltin=True, **kw):
		"""Filter the DPG stack of controls for specific criteria.

		ignoreBuiltin will skip *..##standard control entries i.e. about##standard
		so as to ignore the included default windows.

		filtering on string fields uses full regex matching.
		"""
		exclude = ['aboutwindow', 'docwindow', 'stylewindow', 'debugwindow', 'metricswindow', 'filedialog'] \
			if ignoreBuiltin else []

		if typ:
			if not isinstance(typ, (list, set)):
				typ = [typ]
		else:
			typ = [k for k in self.__cache]
		category = [t for t in typ if t not in exclude and self.__cache.get(t, None)]

		# nothing to filter through...
		if len(category) == 0:
			return []

		ret = []
		for c in category:
			for ctrl in self.__cache[c]:
				items = core.get_item_configuration(ctrl)
				# if filter key not present in item config, pass filter...?
				passed = True
				for k, regex in kw.items():
					val = items.get(k, None)
					if not isinstance(val, str):
						continue

					try:
						regex = re.compile(regex, re.I)
					except re.error as _:
						passed = False
						break
					else:
						if regex.search(val) is None:
							passed = False
							break
				if passed:
					ret.append(ctrl)
		return ret
