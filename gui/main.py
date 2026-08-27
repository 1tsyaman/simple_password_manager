from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from gui.screens.screen_manager import AppScreenManager
from gui.widgets.top_bar import TopBar

from core.pwd_manager import PwdManager

APP_NAME = "Simple Password Manager"

class SimplePasswordManagerApp(MDApp):
	def build(self):
		self.app_screen = MDScreen(
			md_bg_color=self.theme_cls.backgroundColor
		)
		self.box_container = MDBoxLayout(
			orientation="vertical",
			size_hint_max_x="500dp",
			pos_hint={
				"center_x": 0.5
			},
			md_bg_color=self.theme_cls.secondaryContainerColor
		)

		self.top_bar = TopBar(
			title=APP_NAME
		)
		self.screen_manager = AppScreenManager(
			app=self,
			top_bar=self.top_bar,
			pwd_manager=PwdManager()	# dummy pwd manager to initialize vault screen
		)

		self.box_container.add_widget(
			self.top_bar
		)
		self.box_container.add_widget(
			self.screen_manager
		)

		self.app_screen.add_widget(
			self.box_container
		)

		return self.app_screen

if __name__ == "__main__":
	SimplePasswordManagerApp().run()