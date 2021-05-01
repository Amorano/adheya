"""."""

import re
import csv
from dearpygui import core
from adheya import DPGObject
from adheya.layout import Group

class Table(DPGObject):
	def __init__(self, name, **kw):
		super().__init__(name, **kw)

		# row header names to preserve for re-posting table on searching
		self.__headers = []

		# the rows to filter during a search
		self.__rows = []

		self.__filter = '.*'
		# self.__idPanel = f'{self.__guid}-panel'
		self.__panel = Group(self.__idPanel)

	@property
	def filter(self):
		return self.__filter

	@filter.setter
	def filter(self, value):
		newval = value or '.*'
		if newval == self.__filter:
			return
		self.__filter = newval
		self.__tableRefresh()

	def __tableRefresh(self):
		if core.does_item_exist(self.__guid):
			core.delete_item(self.__guid)

		# build the data model so we can search it
		core.add_table(self.__guid, self.__headers, parent=self.__panel.guid)

		searcher = re.compile(self.__filter)
		for row in self.__rows:
			for cell in row:
				if searcher.search(cell):
					core.add_row("table", row)
					break

	def columnAdd(self, col):
		...

	def rowAdd(self, data):
		...

	# @TODO: allow access to cells via __index__?

	def load(self, path):
		"""Load a CSV into the table."""
		with open(path, newline='') as f:
			data = csv.reader(f)
			while header := next(data):
				# skip blank rows in the CSV, first with headers...
				if ''.join(header) != '':
					break
			self.__headers = header
			self.__rows = [d for d in data]
		self.__tableRefresh()

	def save(self, path):
		with open(path, 'w') as f:
			data = csv.writer(f)
			data.writerow(self.__headers)
			data.writerows(self.__rows)
