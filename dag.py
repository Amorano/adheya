"""."""

from dearpygui import core
from adheya.win import WindowMain
from adheya.nodeEditor import NodeEditor

class AdheyaEditor(WindowMain):
	def __init__(self):
		core.set_main_window_size(760, 740)
		core.set_style_item_spacing(2, 1)
		core.set_style_frame_padding(2, 1)
		core.set_style_window_padding(2, 0)
		super().__init__()
		self.__nodeEditor = NodeEditor(self)

	def something(self):
		...

if __name__ == "__main__":
	editor = AdheyaEditor()
	editor.open()
