from collections.abc import Callable

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.textfield import (
	MDTextFieldLeadingIcon,
	MDTextFieldTrailingIcon,
)

from gui.widgets.focusable_text_field import FocusableTextField

class ClickableTrailingIcon(ButtonBehavior, MDTextFieldTrailingIcon):
	pass

class ReadOnlyTextField(MDBoxLayout):
	def __init__(
		self,
		leading_icon: str,
		text: str,
		copy_callback: Callable,
		password: bool = False,
		*args,
		**kwargs
	):
		super().__init__(
			orientation="horizontal",
			adaptive_height=True,
			spacing="4dp",
			*args,
			**kwargs
		)
		self.password = password

		self.field = FocusableTextField(
			MDTextFieldLeadingIcon(
				icon=leading_icon
			),

			text=text,
			readonly=True,	# sets 'is_focusable=False' implicitly
			size_hint_x=1,
			password=password,
			password_mask="\u2022", # "●",
		)

		self.copy_button = MDIconButton(
			icon="content-copy",
			pos_hint={
				"center_x": 0.5,
				"center_y": 0.5,
			},
			on_release=lambda _: copy_callback(self.field.text)
		)

		self.add_widget(self.field)
		self.add_widget(self.copy_button)

	def set_text(self, text: str):
		self.field.text = text

	def get_text(self) -> str:
		return self.field.text

	def set_read_only(self):
		self.field.readonly = True
		if self.password:
			self.field.password = True

	def allow_writing(self):
		self.field.readonly = False
		self.field.is_focusable = True	# Has to be set explicity
		self.field.password = False