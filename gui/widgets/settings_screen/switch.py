from collections.abc import Callable

from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDSwitch

class SwitchSetting(MDBoxLayout):
	def __init__(
		self,
		title				: str,
		value				: bool,
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

		self.add_widget(
			MDLabel(
				text=title,
				pos_hint={"center_y": 0.5}
			)
		)

		switch = MDSwitch(
			pos_hint={"center_y": 0.5}
		)

		switch.active = value
		switch.bind(
			active=set_value_callback
		)

		self.add_widget(switch)