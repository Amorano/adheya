"""."""

import re
import csv
from dearpygui import core, simple
from adheya import DPGObject

class Table(DPGObject):
	def __init__(self, name, **kw):
		super().__init__(name, **kw)

		# row header names to preserve for re-posting table on searching
		self.__headers = []

		# the rows to filter during a search
		self.__rows = []

		self.__filter = re.compile('.*')
		self.__idPanel = f'{self.__guid}-panel'

		with simple.group(self.__idPanel):
			...

	def __tableRefresh(self):
		if core.does_item_exist(self.__guid):
			core.delete_item(self.__guid)

		# build the data model so we can search it
		core.add_table(self.__guid, self.__headers, parent=self.__idPanel)

		for row in self.__rows:
			for cell in row:
				if self.__filter.search(cell):
					core.add_row("table", row)
					break

	@property
	def filter(self, value):
		self.__filter = re.compile(value or '.*', re.I)

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

	def save(self, path):
		with open(path, 'w') as f:
			data = csv.writer(f)
			data.writerow(self.__headers)
			data.writerows(self.__rows)
