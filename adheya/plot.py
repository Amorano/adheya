"""."""

from enum import Enum
from dearpygui import core
from adheya import DPGObject, DPGWrap

class SeriesType(Enum):
	Area = 0,
	Bar = 1,
	Candle = 2,
	Error = 3,
	Heat = 4,
	Hline = 5,
	Image = 6,
	Line = 7,
	Pie = 8,
	Scatter = 9,
	Shade = 10,
	Stair = 11,
	Stem = 12,
	Vline = 13

class Series(DPGObject):
	def __init__(self, guid, parent, series: SeriesType, *arg, **kw):
		kw['parent'] = parent
		super().__init__(guid, **kw)
		cmd = f'add_{series.name.lower()}_series'
		cmd = getattr(core, cmd)
		cmd(self.parent.guid, self.guid, *arg, **kw)

	def delete(self):
		core.delete_series(self.guid)
		DPGObject.delete(self.guid)

@DPGWrap(core.add_plot)
class Plot(DPGObject):
	...
