"""."""

from dearpygui import core
from adheya import DPGObject

class Tree(DPGObject):
	_CMD = core.add_tree

class TreeNode(DPGObject):
	_CMD = core.add_tree_node

class TreeNodeHeader(DPGObject):
	_CMD = core.add_treenode_header
