"""."""

from dearpygui import core
from adheya import DPGObject, DPGWrap

@DPGWrap(core.add_dummy)
class Dummy(DPGObject):
	...

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

@DPGWrap(core.add_group)
class Group(ContextGroup):
	...

@DPGWrap(core.add_spacing)
class SpacingVertical(DPGObject):
	...

@DPGWrap(core.add_same_line)
class SpacingHorizontal(DPGObject):
	...

@DPGWrap(core.add_separator)
class Separator(DPGObject):
	...
