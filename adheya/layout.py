"""."""

from contextlib import contextmanager
from dearpygui import core
from adheya import DPGObject, DPGWrap

class ContextGroup(DPGObject):
	def __enter__(self):
		yield self

	def __exit__(self, *arg, **kw):
		core.end()

class Outline(DPGObject):
	def __init__(self, guid, *arg, **kw):
		super().__init__(guid, *arg, **kw)
		kw['name'] = self.guid
		core.add_indent(**kw)

	def __enter__(self):
		yield self

	def __exit__(self, *arg, **kw):
		core.unindent(name=self.guid)

@DPGWrap(core.add_group)
class Group(ContextGroup):
	...

@DPGWrap(core.add_spacing)
class SpacingVertical(DPGObject):
	...

@DPGWrap(core.add_same_line)
class SpacingHorizontal(DPGObject):
	...

@DPGWrap(core.add_dummy)
class Dummy(DPGObject):
	...


"""
	HAlignNext
	LayoutColumns
	LayoutIndent
	ChildView
"""
