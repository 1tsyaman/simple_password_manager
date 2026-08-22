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

from gui.widgets.ro_text_field import ReadOnlyTextField

class AccountDetailsDialog(MDDialog):
	def __init__(
		self,
		website: str,
		username: str,
		password: str,
		description: str,
		copy_callback: Callable,
		modify_callback: Callable,
		totp_code: str = "",
		totp_callback: Callable | None = None,
		*args,
		**kwargs
	):
		self.copy_callback = copy_callback
		self.modify_callback = modify_callback
		self.totp_callback = totp_callback

		self.website_field = ReadOnlyTextField(
			leading_icon="web",
			text=website,
			copy_callback=copy_callback
		)
		self.username_field = ReadOnlyTextField(
			leading_icon="account",
			text=username,
			copy_callback=copy_callback
		)
		self.password_field = ReadOnlyTextField(
			leading_icon="key",
			text=password,
			copy_callback=copy_callback,
			password=True
		)
		self.description_field = ReadOnlyTextField(
			leading_icon="text",
			text=description,
			copy_callback=copy_callback
		)

		fields = [
			self.website_field,
			self.username_field,
			self.password_field,
			self.description_field,
		]

		# TODO: change this to a special text field with countdown
		# 	use Clock.schedule_intervall(..., 1) in combination with MDLabel to realize counter
		if totp_code != "" and totp_callback is not None:
			self.totp_field = ReadOnlyTextField(
				leading_icon="timer-lock",
				text=totp_code,
				copy_callback=copy_callback
			)

			fields.append(self.totp_field)

		super().__init__(
			MDDialogIcon(
				icon="account-details",
			),

			MDDialogHeadlineText(
				text="Account details"
			),

			MDDialogContentContainer(
				*fields,
				orientation="vertical",
				spacing="12dp"
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(text="Cancel"),
					style="text",
					on_release=lambda _: self.dismiss()
				),

				MDButton(
					MDButtonText(text="Modify"),
					style="text",
					on_release=self._modify
				),
				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _modify(self, instance):
		print("Modified!")