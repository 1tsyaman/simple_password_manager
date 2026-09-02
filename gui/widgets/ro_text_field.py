from collections.abc import Callable
from typing import Any

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.textfield import (
	MDTextFieldLeadingIcon,
)

from gui.widgets.focusable_text_field import FocusableTextField

class ReadOnlyTextField(MDBoxLayout):
	def __init__(
		self,
		leading_icon				: str,
		text						: str,
		copy_callback				: Callable | None = None,	# if no callback is passed, the button is disabled (but visible)
		password					: bool = False,
		trailing_icon				: str = "",
		trailing_callback			: Callable | None = None,
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

		self.copy_callback		= copy_callback
		self.password = password

		self.field = FocusableTextField(
			MDTextFieldLeadingIcon(
				icon=leading_icon,
			),
			trailing_icon=trailing_icon,
			trailing_callback=trailing_callback,

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
			on_release=lambda _: self.button_callback()
		)

		if copy_callback is None:
			self._disable_button(self.copy_button)	

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

	def set_read_write(self):
		self.field.readonly = False
		self.field.is_focusable = True	# Has to be set explicity
		self.field.password = False

	def toggle_password_mask(self):
		self.field.toggle_password_mask()

	def password_mask_is_set(self):
		return self.field.password_mask_is_set()

	def set_trailing_icon(self, icon: str):
		self.field.trailing_icon = icon

	def button_callback(self):
		if self.copy_callback is not None:
			self.copy_callback(self.field.text)

	def _disable_button(
		self,
		button: MDIconButton
	):
		button.opacity = 0.5
		button.disabled = True

	def _enable_button(
		self,
		button: MDIconButton
	):
		button.opacity = 1
		button.disabled = False

class TotpReadOnlyTextField(ReadOnlyTextField):
	def __init__(
		self,
		secondary_icon		: str = "",
		secondary_callback	: Callable | None = None,
		*args,
		**kwargs
	):
		# True -> primary callback: copy, False -> secondary callback
		self.primary_callback	= True
		self.secondary_callback = secondary_callback
		self.secondary_icon		= secondary_icon

		super().__init__(*args, **kwargs)


	def button_callback(self):
		if self.primary_callback:
			if self.copy_callback is not None:
				self.copy_callback(self.field.text[:6])	# only copy the TOTP code
		else:
			if self.secondary_callback is not None:
				self.secondary_callback()

	"""
		Switches copy button between copy and 'secondary' callback and icon
	"""
	def toggle_secondary_callback(self):
		self.primary_callback = not self.primary_callback

		if self.primary_callback:
			self.copy_button.icon = "content-copy"
			enable_condition = self.copy_callback is not None
		else:
			self.copy_button.icon = self.secondary_icon
			enable_condition = self.secondary_callback is not None

		if enable_condition:
			self._enable_button(self.copy_button)
		else:
			self._disable_button(self.copy_button)
