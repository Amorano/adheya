"""."""

from dearpygui import core
from adheya.win import WindowMain
from adheya.node import NodeEditor
from adheya.theme import ThemeManager

class AdheyaEditor(WindowMain):
	def __init__(self):
		core.set_main_window_size(560, 740)
		core.set_style_item_spacing(2, 1)
		core.set_style_frame_padding(2, 1)
		core.set_style_window_padding(2, 0)
		super().__init__()
		self.__nodeEditor = NodeEditor(self)
		self.__theme = ThemeManager(theme="Jovian_Grey")

if __name__ == "__main__":
	editor = AdheyaEditor()
	editor.open()
