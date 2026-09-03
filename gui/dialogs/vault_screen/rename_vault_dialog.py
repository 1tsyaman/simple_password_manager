from collections.abc import Callable

from kivy.uix.widget import Widget

from kivymd.uix.button import (
	MDButton,
	MDButtonText
)
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogHeadlineText,
	MDDialogContentContainer,
	MDDialogButtonContainer,
)

from gui.widgets.input_field import InputField

class RenameVaultDialog(MDDialog):
	def __init__(
		self,
		vault_name: str,
		rename_callback: Callable,
		*args,
		**kwargs
	):
		self.vault_name = vault_name
		self.rename_callback = rename_callback

		self.vault_name_field = InputField(
			title="Vault name",
			icon="safe",
			text=vault_name
		)
		

		super().__init__(
			MDDialogHeadlineText(
				text="Rename vault",
			),

			MDDialogContentContainer(
				self.vault_name_field,
				orientation="vertical"
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(text="Cancel"),
					style="text",
					on_release=lambda *_: self.dismiss()
				),

				MDButton(
					MDButtonText(text="Confirm"),
					style="text",
					on_release=lambda *_: self._rename_callback()
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _rename_callback(self):
		self.dismiss()
		self.rename_callback(
			old_name=self.vault_name,
			new_name=self.vault_name_field.text
		)