from collections.abc import Callable

from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

class TextSetting(MDBoxLayout):
	def __init__(
		self,
		title				: str,
		value				: str,
		set_value_callback	: Callable,
		*args,
		**kwargs
	):
		super().__init__(
			orientation="vertical",
			adaptive_height=True,
			spacing=dp(4),
			*args,
			**kwargs
		)

		self.add_widget(
			MDLabel(
				text=title,
				adaptive_height=True
			)
		)

		field = MDTextField(
			text=value,
			mode="outlined"
		)

		field.bind(
			text=lambda _, text: set_value_callback(text)
		)

		self.add_widget(field)
