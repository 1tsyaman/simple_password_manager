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

class NewVaultDialog(MDDialog):
	def __init__(
		self,
		create_vault_callback: Callable,
		*args,
		**kwargs
	):
		self.name_field				= InputField(title="Name")
		self.password_field			= InputField(title="Password", password=True)
		self.confirm_password_field	= InputField(title="Confirm Password", password=True)
		self.create_vault_callback 	= create_vault_callback

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text="Create vault",
			),

			MDDialogContentContainer(
				self.name_field,
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
					MDButtonText(text="Create"),
					style="text",
					on_release=self._create
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _dismiss(self, _):
		self.dismiss()

	def _create(self, _):
		name			= self.name_field.text
		password		= self.password_field.text
		conf_password	= self.confirm_password_field.text

		self.create_vault_callback(
			dialog=self,
			name=name,
			password=password,
			conf_password=conf_password
		)