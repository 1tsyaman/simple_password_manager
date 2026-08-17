from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang.builder import Builder

from selection_screen import SelectionScreen


class SimplePasswordManagerApp(App):
	# Should return the main widget, the selection screen in this case.
	def build(self):
		self.screen_manager = ScreenManager()
		self.selection_screen = SelectionScreen()

		self.screen_manager.add_widget(self.selection_screen)

		return self.screen_manager

if __name__ == "__main__":
	SimplePasswordManagerApp().run()