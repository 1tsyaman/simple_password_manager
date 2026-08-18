from kivy.lang.builder import Builder
from kivy.uix.widget import Widget

from kivymd.uix.dialog import (
	MDDialog,
	MDDialogButtonContainer,
	MDDialogContentContainer,
	MDDialogHeadlineText,
	MDDialogIcon,
	MDDialogSupportingText,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.textfield import (
	MDTextField,
	MDTextFieldHelperText,
	MDTextFieldHintText,
	MDTextFieldLeadingIcon,
	MDTextFieldMaxLengthText,
	MDTextFieldTrailingIcon,
)

"""
	Possible improvement: different dialogs, different subclasses (with a generic parent class)?
"""
class InputField(MDTextField):
	def __init__(self, *args, password=False, **kwargs):
		if not password:
			return super().__init__(*args, **kwargs)

		if password:
			super().__init__(
				MDTextFieldLeadingIcon(
					icon="lock",
					theme_icon_color="Custom",
					icon_color_normal="mediumaquamarine",
					icon_color_focus="tan",
				),
				MDTextFieldHelperText(
					text="Incorrect password",
					mode="on_error",
				),
				MDTextFieldHintText(
					text="Password",
					text_color_normal="mediumaquamarine",
					text_color_focus="tan",
				),
				mode="outlined",
				fill_color_normal="lightcyan",
				fill_color_focus="lightsteelblue",
				theme_line_color="Custom",
				line_color_normal="mediumaquamarine",
				line_color_focus="tan",
			)

			self.password=password
			self.password_mask="\u2022" # "●"


class LoginDialog(MDDialog):
	def __init__(self, vault, callback, *args, **kwargs):
		self.password_field = InputField(password=True)
		self.vault = vault
		self.callback = callback

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text=f"Unlock {vault}",
			),

			MDDialogContentContainer(
				self.password_field,
				orientation="vertical",
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

	def _dismiss(self, instance):
		self.dismiss()
		self.password_field.text = ""

	def _accept(self, instance):
		password = self.password_field.text
		self.password_field.text = ""

		if self.callback(vault_name=self.vault, password=password):
			return self.dismiss()	# should trigger transition into the new screen, perhaps.

		self.password_field.error = True