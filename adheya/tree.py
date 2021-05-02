"""."""

from dearpygui import core
from adheya import DPGObject, DPGWrap

@DPGWrap(core.add_tab_bar)
class Tree(DPGObject):
	...

@DPGWrap(core.add_tab)
class TreeNode(DPGObject):
	...

@DPGWrap(core.add_tab_button)
class TreeNodeHeader(DPGObject):
	...
