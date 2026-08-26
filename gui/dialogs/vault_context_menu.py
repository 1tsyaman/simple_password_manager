from collections.abc import Callable

from kivy.uix.widget import Widget
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogHeadlineText,
	MDDialogButtonContainer
)

class VaultContextMenu(MDDialog):
	def __init__(
		self,
		vault_name: str,
		open_callback: Callable,
		export_callback: Callable,
		*args,
		**kwargs
	):
		self.vault_name = vault_name

		self.open_callback = open_callback		# open_callback(vault_name: str)
		self.export_callback = export_callback	# export_callback(vault_name: str)

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
			MDDialogHeadlineText(
				text=self.vault_name
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(
						text="Open",
						theme_text_color="Custom",
						text_color=app.theme_cls.errorColor,
					),
					style="text",
					on_release=lambda _: self._open_callback()
				),

				MDButton(
					MDButtonText(
						text="Export",
					),
					style="text",
					on_release=lambda _: self._export_callback()
				),

				Widget(),
				spacing="8dp",

			),
			size_hint=(None, None),
			*args,
			**kwargs
		)

	def update_width(self, *args) -> None:
		self.width = dp(300)

	def _open_callback(self):
		self.dismiss()
		self.open_callback(self.vault_name)

	def _export_callback(self):
		self.dismiss()
		self.export_callback(self.vault_name)