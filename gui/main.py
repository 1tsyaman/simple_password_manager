from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from gui.screens.screen_manager import AppScreenManager

from core.pwd_manager import PwdManager

APP_NAME = "Simple Password Manager"

class SimplePasswordManagerApp(MDApp):
	def build(self):
		self.app_screen = MDScreen(
			md_bg_color=self.theme_cls.backgroundColor
		)

		# Narrow phone screen in the middle of the app window
		self.phone_screen = MDScreen(
			size_hint_max_x="500dp",
    		pos_hint={
				"center_x": 0.5
			},
			md_bg_color=self.theme_cls.secondaryContainerColor
		)
		# Main container that occupies the whole phone screen
		self.main_container = MDBoxLayout(
			orientation="vertical",
			size_hint=(1,1)
		)

		# Top container (contains TopBar or SearchBar)
		self.top_container = MDBoxLayout(
			size_hint_y=None,
			height = "60dp",
		)

		# Occupies the rest of the phone screen
		self.screen_manager = AppScreenManager(
			app=self,
			app_name=APP_NAME,
			phone_screen=self.phone_screen,
			top_container=self.top_container,
			pwd_manager=PwdManager()	# dummy pwd manager to initialize vault screen
		)

		self.main_container.add_widget(
			self.top_container
		)
		self.main_container.add_widget(
			self.screen_manager
		)

		self.phone_screen.add_widget(
			self.main_container
		)
		self.app_screen.add_widget(
			self.phone_screen
		)

		return self.app_screen

if __name__ == "__main__":
	SimplePasswordManagerApp().run()