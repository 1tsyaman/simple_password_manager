from collections.abc import Callable

from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField

class TextSetting(MDBoxLayout):
	def __init__(
		self,
		title						: str,
		value						: str,
		set_value_callback			: Callable,
		text_cleanup_callback		: Callable | None = None,
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

		self.set_value_callback		= set_value_callback
		self.text_cleanup_callback	= text_cleanup_callback

		self.add_widget(
			MDLabel(
				text=title,
				adaptive_height=True
			)
		)

		self.field = MDTextField(
			text=value,
			mode="outlined"
		)

		self.field.bind(
			text=lambda _, text: self._set_value(text)
		)

		self.add_widget(self.field)

	def _set_value(
		self,
		value: str
	):
		if self.text_cleanup_callback is not None:
			value = self.text_cleanup_callback(value)

			# only update if we changed the user's input
			if value != self.field.text:
				self.field.text = value
				return

		# only set the value once after clean up
		self.set_value_callback(value)