"""."""

from dearpygui import core
from adheya import DPGObject

class Dummy(DPGObject):
	_CMD = core.add_radio_button

class ContextGroup(DPGObject):
	def __enter__(self):
		yield self

	def __exit__(self, *arg, **kw):
		core.end()

class Outline(DPGObject):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		kw['name'] = self.label
		core.add_indent(**kw)

	def __enter__(self):
		yield self

	def __exit__(self, *arg, **kw):
		core.unindent(name=self.label)

class Group(ContextGroup):
	def __init__(self, parent, **kw):
		super().__init__(parent, **kw)
		kw['parent'] = self.parent.guid
		core.add_group(self.guid, **kw)
		core.end()

class SpacingVertical(DPGObject):
	_CMD = core.add_spacing
	_GUID = False

class SpacingHorizontal(DPGObject):
	_CMD = core.add_same_line
	_GUID = False

class Separator(DPGObject):
	_CMD = core.add_separator
