"""."""

from dearpygui import core
from adheya import DPGObject, DPGWrap

@DPGWrap(core.add_tab_bar)
class Canvas(DPGObject):
	...
