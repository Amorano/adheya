"""."""

import re
from dearpygui import core, simple
from adheya import DPGObject, Singleton, CallbackType
from adheya.theme import ThemeManager

class WindowMain(DPGObject, metaclass=Singleton):
	def __init__(self, name=None, **config):

		super().__init__(name, **config)

		self.__cache = {}
		self.__callbacks = {k: [] for k in CallbackType}

		with simple.window(self.guid, **config):
			...

		core.set_exit_callback(self.__exit)
		# close event as well -- can register for "close"/"exit"

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

		self.__theme = ThemeManager(theme="Jovian_Grey")
		self.__cacheRefresh()

	@property
	def cache(self):
		return self.__cache

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

	def __callback(self, sender, data, event):
		for cmd in self.__callbacks[event]:
			cmd(sender, data)

	def __exit(self, sender, data):
		core.stop_dearpygui()

	def register(self, callback: CallbackType, destination):
		what = self.__callbacks.get(callback, None)
		if what is None:
			raise Exception(f"no event {callback}")

		if destination not in what:
			what.append(destination)
			self.__callbacks[callback] = what

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

	def open(self):
		core.start_dearpygui(primary_window=self.guid)
