"""."""

import json
import os.path
from dearpygui import core
from adheya.win import Window
from adheya.general import ListBox

class ThemeManager(Window):
	def __init__(self, theme=None, root=None):
		self.__theme = {}
		self.__current = theme
		super().__init__(label='Theme Manager', autosize=True)

		self.mainbar.show = False

		if root is None:
			root = os.path.dirname(os.path.realpath(__file__))
			root = f'{root}/theme.json'
		self.__load(root)

		themes = self.themes
		ListBox(self, label="", items=self.themes, num_items=len(themes),
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

	@property
	def current(self):
		"""Selected theme's data blob."""
		return self.__theme[self.__current]

	@property
	def themes(self):
		return list(sorted(self.__theme.keys()))

	def apply(self, who):
		theme = self.__theme.get(who, None)
		if theme is None:
			core.log_error(f"no theme: {who}")
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
					core.log_error(f"no function: {meth}")
					continue

				if const:
					nv = f"mvGuiCol_{k}"
					try:
						nv = getattr(core, nv)
					except Exception as _:
						core.log_error(f"no constant: {nv}")
						continue
					v = [nv] + [int(c * 255) for c in v]

				if isinstance(v, (list, tuple)):
					meth(*v)
				else:
					meth(v)
		self.__current = who

if __name__ == "__main__":
	window = ThemeManager()
	window.open()
