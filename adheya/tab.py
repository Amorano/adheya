"""."""

from dearpygui import core
from adheya import DPGObject

class TabBar(DPGObject):
	_CMD = core.add_tab_bar

class Tab(DPGObject):
	_CMD = core.add_tab

class TabButton(DPGObject):
	_CMD = core.add_tab_button
