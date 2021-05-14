"""."""

from dearpygui import core
import adheya as aha

class Editor():
	def __init__(self):
		with aha.Window() as w:
			print(w)
			m = w.mainbar.add('file')
			m.addItem('load', callback=self.__load)
			m.addItem('save', callback=self.__save)
		w.open()

	def __load(self):
		...

	def __save(self):
		...

if __name__ == '__main__':
	# can be either way -- context or manual parent
	editor = Editor()
