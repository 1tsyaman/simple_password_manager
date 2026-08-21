from kivy.lang.builder import Builder
from kivy.uix.widget import Widget

from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogButtonContainer,
	MDDialogContentContainer,
	MDDialogHeadlineText,
	MDDialogIcon,
	MDDialogSupportingText,
)
from kivymd.uix.textfield import (
	MDTextField,
	MDTextFieldHelperText,
	MDTextFieldHintText,
	MDTextFieldLeadingIcon,
	MDTextFieldMaxLengthText,
	MDTextFieldTrailingIcon,
)

"""
	To communicate incorrect input:
		input = InputField(...)
		...
		input.error_widget.text = "Some error meesage"
		input.error = True
"""
class InputField(MDTextField):
	def __init__(self, *args, title: str, icon: str = "", password=False, **kwargs):
		self.error_widget = MDTextFieldHelperText(text="Initial message", mode="on_error")

		super().__init__(
			MDTextFieldLeadingIcon(
				icon=icon,
				theme_icon_color="Custom",
				icon_color_normal="mediumaquamarine",
				icon_color_focus="tan",
			),
			self.error_widget,
			MDTextFieldHintText(
				text=title,
				text_color_normal="mediumaquamarine",
				text_color_focus="tan",
			),
			*args,
			mode="outlined",
			fill_color_normal="lightcyan",
			fill_color_focus="lightsteelblue",
			theme_line_color="Custom",
			line_color_normal="mediumaquamarine",
			line_color_focus="tan",
			**kwargs
		)

		self.password=password
		self.password_mask="\u2022" # "●"


class LoginDialog(MDDialog):
	def __init__(self, vault, login_callback, *args, **kwargs):
		self.password_field = InputField(title="Password", icon="lock", password=True)
		self.loading_indicator = MDCircularProgressIndicator(
			size_hint=(None, None),
			pos_hint={"center_x": 0.5},
			size=("32dp", "32dp"), 
			active=False,	# active -> visible
		)

		self.vault = vault
		self.login_callback = login_callback

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text=f"Unlock {vault}",
			),

			MDDialogContentContainer(
				self.password_field,
				self.loading_indicator,
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

	def _dismiss(self, instance):
		self.dismiss()
		self.password_field.text = ""

	def _accept(self, instance):
		password = self.password_field.text
		self.password_field.text = ""

		self.login_callback(login_dialog=self, vault_name=self.vault, password=password)

class NewVaultDialog(MDDialog):
	def __init__(self, create_vault_callback, *args, **kwargs):
		self.name_field				= InputField(title="Name")
		self.password_field			= InputField(title="Password", password=True)
		self.confirm_password_field	= InputField(title="Confirm Password", password=True)
		self.create_vault_callback 		= create_vault_callback

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text=f"Create vault",
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

	def _dismiss(self, instance):
		self.dismiss()
		self.name_field.text = ""
		self.password_field.text = ""
		self.confirm_password_field.text = ""

	def _create(self, instance):
		name			= self.name_field.text
		password		= self.password_field.text
		conf_password	= self.confirm_password_field.text

		if self.create_vault_callback(dialog=self, name=name, password=password, conf_password=conf_password):
			self.name_field.text = ""
			self.password_field.text = ""
			self.confirm_password_field.text = ""
			return self.dismiss()


class NewAccountDialog(MDDialog):
	def __init__(self, add_account_callback, *args, **kwargs):
		self.website_field				= InputField(title="Website")
		self.username_field				= InputField(title="Username")
		self.password_field				= InputField(title="Password", password=True)
		self.description_field			= InputField(title="Description")
		self.add_account_callback		= add_account_callback

		super().__init__(
			MDDialogIcon(
				icon="account",
			),

			MDDialogHeadlineText(
				text=f"Add new account",
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
		self.website_field.text = ""
		self.username_field.text = ""
		self.password_field.text = ""
		self.description_field.text = ""

	def _add(self, instance):
		website			= self.website_field.text
		username		= self.username_field.text
		password		= self.password_field.text
		description		= self.description_field.text

		self.add_account_callback(dialog=self, website=website, username=username,
							   		password=password, description=description)