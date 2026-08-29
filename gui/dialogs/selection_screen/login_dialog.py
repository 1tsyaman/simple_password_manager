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

class LoginDialog(MDDialog):
	def __init__(
		self,
		vault: str,
		login_callback: Callable,
		*args,
		**kwargs
	):
		self.password_field = InputField(
			title="Password",
			icon="lock",
			password=True,
			trailing_icon="eye",
			trailing_callback=self.toggle_password_mask
		)
		self.vault = vault
		self.login_callback = login_callback

#		self.loading_indicator = MDCircularProgressIndicator(	We don't need loading indicator for now
#			size_hint=(None, None),
#			pos_hint={"center_x": 0.5},
#			size=("32dp", "32dp"), 
#			active=False,	# active -> visible
#		)

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text=f"Unlock {vault}",
			),

			MDDialogContentContainer(
				self.password_field,
#				self.loading_indicator,
				orientation="vertical",
				spacing="10dp",
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(text="Cancel"),
					style="text",
					on_release=self._dismiss
				),

				MDButton(
					MDButtonText(text="Accept"),
					style="text",
					on_release=self._accept
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _dismiss(self, _):
		self.dismiss()

	def _accept(self, _):
		password = self.password_field.text
		self.login_callback(
			dialog=self,
			vault_name=self.vault,
			password=password
		)

	def toggle_password_mask(self):
		self.password_field.toggle_password_mask()
		# Toggle the icon
		if self.password_field.password_mask_is_set():
			self.password_field.trailing_icon = "eye"
		else:
			self.password_field.trailing_icon = "eye-off"
