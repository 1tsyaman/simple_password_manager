from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.divider import MDDivider

class SettingSection(MDBoxLayout):
	def __init__(
		self,
		title: str,
		*args,
		**kwargs
	):
		super().__init__(
			orientation="vertical",
			adaptive_height=True,
			spacing=dp(6),
			padding=(0, dp(20), 0, dp(8)),
			*args,
			**kwargs
		)

		app = MDApp.get_running_app()
		assert app is not None

		self.add_widget(
			MDLabel(
				text=title,
				font_style="Title",
				role="large",
				theme_text_color="Custom",
				text_color=app.theme_cls.primaryColor,
				adaptive_height=True
			)
		)
		self.add_widget(
			MDDivider()
		)