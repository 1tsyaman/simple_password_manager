from kivy.lang.builder import Builder

from kivymd.app import MDApp
from kivymd.uix.appbar import MDTopAppBar

from gui.selection_screen import SelectionScreen

class TopBar(MDTopAppBar):
	pass


class SimplePasswordManagerApp(MDApp):
	# Should return the main widget, the selection screen in this case.
	def build(self):
		# Init top bar
		Builder.load_file("top_bar.kv")

		return Builder.load_file("main.kv")

if __name__ == "__main__":
	SimplePasswordManagerApp().run()