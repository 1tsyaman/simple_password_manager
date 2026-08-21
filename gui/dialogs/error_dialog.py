from collections.abc import Callable

from kivy.uix.widget import Widget

from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogButtonContainer,
	MDDialogHeadlineText,
	MDDialogSupportingText,
	MDDialogIcon
)

"""
	Callback functions should take an argument dialog: ErrorDialog
"""
class ErrorDialog(MDDialog):
	def __init__(
		self,
		error_title: str,
		error_message: str,
		first_button_label: str = "dismiss",
		second_button_label: str = "",
		first_button_callback: Callable | None = None,
		second_button_callback: Callable | None = None,
		*args,
		**kwargs
	):

		self.first_button_callback = first_button_callback
		self.second_button_callback = second_button_callback

		buttons = []
		buttons.append(
			MDButton(
				MDButtonText(text=first_button_label),
				style="text",
				on_release=self._first_callback
			)
		)

		if second_button_label != "":
			buttons.append(
				MDButton(
					MDButtonText(text=second_button_label),
					style="text",
					on_release=self._second_callback
				)
			)

		super().__init__(
			MDDialogIcon(
				icon="alert-circle",
			),

			MDDialogHeadlineText(
				text=error_title,
			),

			MDDialogSupportingText(
				text=error_message
			),

			MDDialogButtonContainer(
				Widget(),
				*buttons,			# unpack array of buttons
				spacing="8dp",
			),

			*args,
			**kwargs,
		)

	def _first_callback(self, _):
		if self.first_button_callback is not None:
			self.first_button_callback(dialog=self)

	def _second_callback(self, _):
		if self.second_button_callback is not None:
			self.second_button_callback(dialog=self)