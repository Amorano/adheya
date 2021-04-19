"""."""

from dearpygui import core
from adheya.win import WindowMain
from adheya.nodeEditor import NodeEditor

class AdheyaEditor(WindowMain):
	def __init__(self):
		core.set_main_window_size(1280, 840)
		core.set_style_item_spacing(2, 1)
		core.set_style_frame_padding(2, 1)
		core.set_style_window_padding(2, 0)
		super().__init__()
		self.__nodeEditor = NodeEditor(parent=self)

if __name__ == "__main__":
	editor = AdheyaEditor()
	core.start_dearpygui(primary_window=editor.guid)
