from collections.abc import Callable

from kivy.uix.widget import Widget

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogIcon,
	MDDialogHeadlineText,
	MDDialogContentContainer,
	MDDialogButtonContainer
)

from gui.widgets.input_field import InputField

class ChangePasswordDialog(MDDialog):
	def __init__(
		self,
		change_password_callback: Callable,
		*args,
		**kwargs
	):
		self.password_field				= InputField(title="New Password", password=True)
		self.confirm_password_field		= InputField(title="Confirm New Password", password=True)
		self.change_password_callback 	= change_password_callback

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text="Change vault password",
			),

			MDDialogContentContainer(
				self.password_field,
				self.confirm_password_field,
				orientation="vertical",
				spacing="30dp"
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(text="Cancel"),
					style="text",
					on_release=self._dismiss
				),

				MDButton(
					MDButtonText(text="Confirm"),
					style="text",
					on_release=self._confirm
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _dismiss(self, _):
		self.dismiss()

	def _confirm(self, _):
		password		= self.password_field.text
		conf_password	= self.confirm_password_field.text

		self.change_password_callback(
			dialog=self,
			password=password,
			conf_password=conf_password
		)