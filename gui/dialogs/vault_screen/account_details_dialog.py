from collections.abc import Callable

from kivy.clock import Clock
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogIcon,
	MDDialogHeadlineText,
	MDDialogContentContainer,
	MDDialogButtonContainer
)

from gui.widgets.ro_text_field import (
	ReadOnlyTextField,
	TotpReadOnlyTextField,
	PasswordReadOnlyText
)
from gui.widgets.vault_screen.account_list import AccountEntry
from gui.dialogs.yes_no_dialog import YesNoDialog

class AccountDetailsDialog(MDDialog):
	def __init__(
		self,
		website					: str,
		username				: str,
		password				: str,
		description				: str,
		copy_callback			: Callable,
		totp_qr_callback		: Callable[..., str],
		modify_callback			: Callable,				# accepts an optional uri: str option
		delete_callback			: Callable,
		account_entry			: AccountEntry,
		totp_code				: str = "",
		totp_time_remaining		: int = 0,
		totp_callback			: Callable | None = None,
		*args,
		**kwargs
	):
		# Save original details
		self.website		= website
		self.username		= username
		self.password		= password
		self.description	= description
		self.totp_code		= totp_code
		self.time_remaining = totp_time_remaining

		# For updating the labels on the vault screen
		self.account_entry	= account_entry
		self.totp_uri		= None			# attribute to store new uri

		# Save callbacks
		self.copy_callback			= copy_callback
		self.totp_qr_callback		= totp_qr_callback
		self.modify_callback		= modify_callback
		self.delete_callback		= delete_callback
		self.totp_callback			= totp_callback

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
		self.password_field = PasswordReadOnlyText(
			leading_icon="key",
			text=password,
			copy_callback=copy_callback,
		)
		self.description_field = ReadOnlyTextField(
			leading_icon="text",
			text=description,
			copy_callback=copy_callback
		)

		if totp_code != "":
			self.totp_field = TotpReadOnlyTextField(
				leading_icon="timer-lock",
				text=self._format_totp_string(),
				copy_callback=copy_callback,
				secondary_icon="qrcode",
				secondary_callback=lambda *_: totp_qr_callback(details_dialog=self)
			)

			# Set up a thread to update the code/timer
			Clock.schedule_interval(
				lambda *_: self.update_totp_field(),
				1,	# once a second
			)

		else:
			self.totp_field = TotpReadOnlyTextField(
				leading_icon="timer-lock",
				text="TOTP not configured",
				secondary_icon="qrcode",
				secondary_callback=lambda *_: totp_qr_callback(details_dialog=self)
			)

		fields = [
			self.website_field,
			self.username_field,
			self.password_field,
			self.description_field,
			self.totp_field,
		]

		# Store a reference for the button labels for modification
		self.dismiss_button_label = MDButtonText(text="Cancel")		
		self.modify_button_label= MDButtonText(text="Modify")

		# Get app for the app themes
		app = MDApp.get_running_app()
		assert app is not None

		# Store a reference for the button to be able to disable it when in modification view
		self.delete_button = MDButton(
			MDButtonText(
				text="Delete",
				theme_text_color="Custom",
    			text_color=app.theme_cls.errorColor,
			),
			style="text",
			on_release=self.show_delete_confirmation_dialog
		)

		# Modification state (determines the behaviours of the buttons)
		self.modification_in_process = False

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
					self.dismiss_button_label,
					style="text",
					on_release=self._dismiss_or_cancel
				),

				MDButton(
					self.modify_button_label,
					style="text",
					on_release=self._modify_or_save
				),

				self.delete_button,

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def update_totp_field(self):
		if self.time_remaining == 0 and self.totp_callback is not None:
			self.totp_code, self.time_remaining = self.totp_callback()
		else:
			self.time_remaining -= 1

		self.totp_field.set_text(self._format_totp_string())

	def _modify(self):
		self.modification_in_process = True
		self._toggle_modification_mode()

	def _save(self):
		new_website = self.website_field.get_text()
		new_username = self.username_field.get_text()
		new_password = self.password_field.get_text()
		new_totp_code = self.totp_field.get_text()
		new_description = self.description_field.get_text()

		if not self.modify_callback(
			website=self.website,
			username=self.username,
			new_website=new_website,
			new_username=new_username,
			new_password=new_password,
			new_description=new_description,
			new_totp_uri=self.totp_uri,
		):
			return

		# Update stored values
		self.website		= new_website
		self.username		= new_username
		self.password		= new_password
		self.totp_code		= new_totp_code
		self.description	= new_description

		if self.totp_uri is not None:
			# Enable the copy button
			self.totp_field.copy_callback = self.copy_callback


		self.modification_in_process = False
		self._toggle_modification_mode()

	def _cancel(self):
		# Restore original values
		self.website_field.set_text(self.website)
		self.username_field.set_text(self.username)
		self.password_field.set_text(self.password)
		self.totp_field.set_text(self.totp_code)
		self.description_field.set_text(self.description)

		self.totp_uri = None

		self.modification_in_process = False
		self._toggle_modification_mode()

	def _modify_or_save(self, instance):
		if not self.modification_in_process:
			self._modify()
		else:
			self._save()

	def _dismiss_or_cancel(self, instance):
		if not self.modification_in_process:
			self.dismiss()
		else:
			self._cancel()

	def show_delete_confirmation_dialog(self, instance):
		YesNoDialog(
			headline="Are you sure?",
			message="Deleted accounts cannot be restored",
			yes_callback=lambda _:self._delete(),
			icon="alert-circle" 
		).open()

	def _delete(self):
		self.delete_callback(
			website=self.website,
			username=self.username,
			account_entry=self.account_entry
		)

		self.dismiss()

	def set_totp_preview_uri(
		self,
		uri: str,
		preview_code: str
	):
		self.totp_uri = uri
		self.totp_field.set_text(preview_code)

	def _toggle_modification_mode(self):
		if self.modification_in_process:
			# Allow modifying
			self.website_field.set_read_write()
			self.username_field.set_read_write()
			self.password_field.set_read_write()
			self.totp_field.toggle_secondary_callback()
			self.description_field.set_read_write()

			# Change the button labels
			self.dismiss_button_label.text	= "Cancel"
			self.modify_button_label.text	= " Save "

			# Disable the delete button
			self.delete_button.disabled = True
			self.delete_button.opacity = 0.5
		else:
			# Disable modification
			self.website_field.set_read_only()
			self.username_field.set_read_only()
			self.password_field.set_read_only()
			self.totp_field.toggle_secondary_callback()
			self.description_field.set_read_only()

			# Change the button labels back
			self.dismiss_button_label.text	= "Dismiss"
			self.modify_button_label.text	= "Modify "

			# Enable the delete button
			self.delete_button.disabled = False
			self.delete_button.opacity = 1

	def _format_totp_string(self) -> str:
		return f"{self.totp_code[:3]} {self.totp_code[3:]}   •   {self.time_remaining:02d}s"	# pad with 0s to 2 digits