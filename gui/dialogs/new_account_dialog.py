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

from core.pwd_manager import PwdManager

class NewAccountDialog(MDDialog):
	def __init__(
		self,
		add_account_callback: Callable,
		*args,
		**kwargs
	):
		self.website_field				= InputField(title="Website")
		self.username_field				= InputField(title="Username")
		self.password_field				= InputField(title="Password")
		self.description_field			= InputField(title="Description")
		self.add_account_callback		= add_account_callback

		self.password_field.text = PwdManager.generate_pwd()	# Auto-fill with random password

		super().__init__(
			MDDialogIcon(
				icon="account",
			),

			MDDialogHeadlineText(
				text="Add new account",
			),

			MDDialogContentContainer(
				self.website_field,
				self.username_field,
				self.password_field,
				self.description_field,
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
					MDButtonText(text="Add"),
					style="text",
					on_release=self._add
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _dismiss(self, instance):
		self.dismiss()

	def _add(self, instance):
		website			= self.website_field.text
		username		= self.username_field.text
		password		= self.password_field.text
		description		= self.description_field.text

		self.add_account_callback(
			dialog=self,
			website=website,
			username=username,
			password=password,
			description=description
		)