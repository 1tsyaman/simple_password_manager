from collections.abc import Callable

from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu

class ChoiceMenu(MDDropdownMenu):
	"""
		Make the menu originate from the button, instead from the corner somewhere
	"""
	def on_open(self, *args):
		self.scale_value_center = self._start_coords
		super().on_open(*args)

class ChoiceSetting(MDBoxLayout):
	def __init__(
		self,
		title				: str,
		value				: str,
		options				: list[str],
		set_value_callback	: Callable,
		*args,
		**kwargs
	):
		super().__init__(
			size_hint_y=None,
			height=dp(56),
			*args,
			**kwargs
		)

		self.set_value_callback = set_value_callback

		self.add_widget(
			MDLabel(
				text=title,
				pos_hint={"center_y": 0.5}
			)
		)

		self.button_text = MDButtonText(text=value)

		button = MDButton(
			self.button_text,
			style="text",
			pos_hint={"center_y": 0.5}
		)

		self.menu = ChoiceMenu(
			caller=button,
			items=[
				{
					"text": option,
					"on_release":
						lambda option=option: self._select(option)
				}
				for option in options
			]
		)

		button.bind(
			on_release=lambda *_: self.menu.open()
		)

		self.add_widget(button)

	def _select(self, value: str):
		self.button_text.text = value
		self.menu.dismiss()
		self.set_value_callback(value)
