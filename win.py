"""."""

import re
import json
import os.path
from dearpygui import core, simple
from dpgo import DPGObject, Singleton

class WindowMain(DPGObject, metaclass=Singleton):
	def __init__(self, **config):

		super().__init__(None, **config)

		self.__cache = {}
		self.__callbacks = {
			'render': [],
			'resize': [],
			'mouse_down': [],
			'mouse_drag': [],
			'mouse_move': [],
			'mouse_double_click': [],
			'mouse_click': [],
			'mouse_release': [],
			'mouse_wheel': [],
			'key_down': [],
			'key_press': [],
			'key_release': [],
			'accelerator': []
		}

		with simple.window(self.guid, **config):
			...

		core.set_exit_callback(self.__exit)
		# close event as well -- can register for "close"/"exit"

		core.set_render_callback(lambda x: self.__callback(x, 'render'))
		core.set_resize_callback(lambda x: self.__callback(x, 'resize'))
		core.set_mouse_down_callback(lambda x: self.__callback(x, 'mouse_down'))
		core.set_mouse_drag_callback(lambda x: self.__callback(x, 'mouse_drag'), 10)
		core.set_mouse_move_callback(lambda x: self.__callback(x, 'mouse_move'))
		core.set_mouse_double_click_callback(lambda x: self.__callback(x, 'mouse_double_click'))
		core.set_mouse_click_callback(lambda x: self.__callback(x, 'mouse_click'))
		core.set_mouse_release_callback(lambda x: self.__callback(x, 'mouse_release'))
		core.set_mouse_wheel_callback(lambda x: self.__callback(x, 'mouse_wheel'))
		core.set_key_down_callback(lambda x: self.__callback(x, 'key_down'))
		core.set_key_press_callback(lambda x: self.__callback(x, 'key_press'))
		core.set_key_release_callback(lambda x: self.__callback(x, 'key_release'))
		core.set_accelerator_callback(lambda x: self.__callback(x, 'accelerator'))

		self.__theme = ThemeManager(theme="Jovian_Grey")
		self.__cacheRefresh()

	def open(self):
		core.start_dearpygui(primary_window=self.guid)

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

	def register(self, callback, destination):
		what = self.__callbacks.get(callback, None)
		if what is None:
			return
		if destination not in what:
			what.append(destination)
			self.__callbacks[callback] = what

	def __exit(self, sender, data):
		core.stop_dearpygui()

	def __callback(self, sender, data):
		for cmd in self.__callbacks[data]:
			print(cmd, sender, data)

class ThemeManager():
	def __init__(self, theme=None, root=None):
		self.__current = theme
		if root is None:
			root = os.path.dirname(os.path.realpath(__file__))
			root = f'{root}/theme.json'
		self.__load(root)

		with simple.window("theme", autosize=True):
			themes = self.themes
			core.add_listbox("themes", label="",
				items=themes,
				num_items=len(themes),
				callback=self.__themeChange)

		self.apply(theme or self.__current)

	def __themeChange(self, sender):
		idx = core.get_value(sender)
		theme = self.themes[idx]
		self.apply(theme)

	def __load(self, root=None, clear=True):
		if clear:
			self.__theme = {}
		if root is None:
			root = os.path.dirname(os.path.realpath(__file__))

		if not os.path.exists(root):
			return

		with open(root) as fp:
			self.__theme = json.load(fp)

		# default
		k = [k for k in self.__theme]
		theme = k[0] if len(k) else None
		self.apply(theme)

	def __str__(self):
		size = len(self.__theme.keys())
		return f"[{self.__current}] {size} themes"

	@property
	def current(self):
		"""Selected theme's data blob."""
		return self.__theme[self.__current]

	@property
	def themes(self):
		return sorted(self.__theme.keys())

	def apply(self, who):
		theme = self.__theme.get(who, None)
		if theme is None:
			print(f"no theme: {who}")
			return

		overall = theme.get("theme", None)
		if overall:
			core.set_theme(theme=overall)

		# thing is what category, cmd is cmd, const == color const for v[0]
		# func == extend function with data...
		for thing, cmd, func, const in [
			# ("font", "add_additional_font", False, False),
			("style", "set_style_", True, False),
			("color", "set_theme_item", False, True),
		]:
			for k, v in theme.get(thing, {}).items():
				meth = f"{cmd}{k}" if func else cmd
				try:
					meth = getattr(core, meth)
				except Exception as _:
					print(f"no function: {meth}")
					continue

				if const:
					nv = f"mvGuiCol_{k}"
					try:
						nv = getattr(core, nv)
					except Exception as _:
						print(f"no constant: {nv}")
						continue
					v = [nv] + [int(c * 255) for c in v]

				if isinstance(v, (list, tuple)):
					meth(*v)
				else:
					meth(v)
		self.__current = who
