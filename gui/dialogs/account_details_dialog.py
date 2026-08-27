from collections.abc import Callable

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

from gui.widgets.ro_text_field import ReadOnlyTextField
from gui.widgets.account_list import AccountEntry
from gui.dialogs.yes_no_dialog import YesNoDialog

class AccountDetailsDialog(MDDialog):
	def __init__(
		self,
		website: str,
		username: str,
		password: str,
		description: str,
		copy_callback: Callable,
		modify_callback: Callable,
		delete_callback: Callable,
		account_entry: AccountEntry,
		totp_code: str = "",
		totp_time_remaining: int = 0,
		totp_callback: Callable | None = None,
		*args,
		**kwargs
	):
		# Save original details
		self.website = website
		self.username = username
		self.password = password
		self.description = description

		# For updating the labels on the vault screen
		self.account_entry = account_entry

		# Save callbacks
		self.copy_callback = copy_callback
		self.modify_callback = modify_callback
		self.delete_callback = delete_callback
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
			password=True,
			trailing_icon="eye",
			trailing_callback=self.toggle_password_mask
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


	def _modify(self):
		self.modification_in_process = True
	
		# Allow modifying
		self.website_field.allow_writing()
		self.username_field.allow_writing()
		self.password_field.allow_writing()
		self.description_field.allow_writing()

		# Change the button labels
		self.dismiss_button_label.text	= "Cancel"
		self.modify_button_label.text	= "Save"

		# Disable the delete button
		self.delete_button.disabled = True
		self.delete_button.opacity = 0.5

	def _save(self):
		new_website = self.website_field.get_text()
		new_username = self.username_field.get_text()
		new_password = self.password_field.get_text()
		new_description = self.description_field.get_text()

		if not self.modify_callback(
			website=self.website,
			username=self.username,
			new_website=new_website,
			new_username=new_username,
			new_password=new_password,
			new_description=new_description,
			account_entry=self.account_entry,
		):
			return

		self.modification_in_process = False
		# Update stored values
		self.website = new_website
		self.username = new_username
		self.password = new_password
		self.description = new_description

		# Disable modification
		self.website_field.set_read_only()
		self.username_field.set_read_only()
		self.password_field.set_read_only()
		self.description_field.set_read_only()

		# Change the button labels back
		self.dismiss_button_label.text	= "Dismiss"
		self.modify_button_label.text	= "Modify"

		# Enable the delete button
		self.delete_button.disabled = False
		self.delete_button.opacity = 1

	def _cancel(self):
		self.modification_in_process = False

		# Restore original values
		self.website_field.set_text(self.website)
		self.username_field.set_text(self.username)
		self.password_field.set_text(self.password)
		self.description_field.set_text(self.description)

		# Disable modification
		self.website_field.set_read_only()
		self.username_field.set_read_only()
		self.password_field.set_read_only()
		self.description_field.set_read_only()

		# Change the button labels back
		self.dismiss_button_label.text	= "Dismiss"
		self.modify_button_label.text	= "Modify"

		# Enable the delete button
		self.delete_button.disabled = False
		self.delete_button.opacity = 1

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
			no_callback=lambda dialog: dialog.dismiss(),
			yes_callback=self._delete,
			icon="alert-circle" 
		).open()

	def _delete(self, dialog):
		self.delete_callback(
			website=self.website,
			username=self.username,
			account_entry=self.account_entry
		)

		dialog.dismiss()
		self.dismiss()

	def toggle_password_mask(self):
		self.password_field.toggle_password_mask()
		# Toggle the icon
		if self.password_field.password_mask_is_set():
			self.password_field.set_trailing_icon("eye")
		else:
			self.password_field.set_trailing_icon("eye-off")