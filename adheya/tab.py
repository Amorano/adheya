"""."""

from dearpygui import core
from adheya import DPGObject, DPGWrap

@DPGWrap(core.add_tab_bar)
class TabBar(DPGObject):
	...

@DPGWrap(core.add_tab)
class Tab(DPGObject):
	...

@DPGWrap(core.add_tab_button)
class TabButton(DPGObject):
	...
