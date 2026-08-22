from typing import TYPE_CHECKING

from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.appbar import MDActionTopAppBarButton

from gui.widgets.top_bar import TopBar
from gui.widgets.labels import NoVaultsLabel
from gui.widgets.input_field import InputField
from gui.widgets.vault_list import VaultEntry, VaultList
from gui.dialogs.login_dialog import LoginDialog
from gui.dialogs.new_vault_dialog import NewVaultDialog

import storage.io as io
from core.errors import (
	PasswordRequirementsError,
	KeyLengthError,
	KeyDerivationError,
	log
)

# to avoid cicular import issues
if TYPE_CHECKING:
	from gui.screens.screen_manager import AppScreenManager

class SelectionScreen(MDScreen):
	def __init__(
		self,
		app_data_path: str,
		screen_manager: "AppScreenManager",	# forward reference for type checking
		top_bar: TopBar,
		*args,
		**kwargs
	):
		self.app_data_path = app_data_path
		self.screen_manager = screen_manager
		self.top_bar = top_bar

		self.box_container = MDBoxLayout(
			orientation="vertical"
		)

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
			self.box_container,
			name="selection",
			md_bg_color=app.theme_cls.secondaryContainerColor,
			*args,
			**kwargs
		)

	def on_pre_enter(self, *args):
		self.refresh()

	"""
		is called before entering the screen
	"""
	def refresh(self):
		top_bar: TopBar = self.top_bar
		back_button: MDActionTopAppBarButton = top_bar.back_button

		# Disable back button
		top_bar.back_callback = None
		back_button.disabled = True
		back_button.opacity = 0

		# New vault button
		top_bar.plus_callback = self.show_new_vault_dialog

		self.load_vaults()

	def load_vaults(self):
		# refresh vault list
		app_data_path = self.app_data_path
		container : MDBoxLayout = self.box_container
		self.vaults = io.get_vault_list(app_data_path)

		if len(self.vaults) == 0:
			# Add no_vaults_label
			container.clear_widgets()
			container.add_widget(NoVaultsLabel())
			return

		vault_list = VaultList()

		for vault in self.vaults:
			entry = VaultEntry(name=vault)
			entry.bind(on_release=self.show_open_vault_dialog)

			vault_list.add_vault(entry)

		container.clear_widgets()
		container.add_widget(vault_list)

	def on_leave(self, *args):
		self.clear()

	"""
		is called when leaving the screen
	"""
	def clear(self):
		self.box_container.clear_widgets()
		self.box_container.add_widget(NoVaultsLabel())

##	New Vault Functions	##

	def show_new_vault_dialog(self):
		NewVaultDialog(create_vault_callback=self.create_vault).open()

	def create_vault(
		self,
		dialog: NewVaultDialog,
		name: str,
		password: str,
		conf_password: str
	):
		name_field 				: InputField = dialog.name_field
		password_field			: InputField = dialog.password_field
		confirm_password_field	: InputField = dialog.confirm_password_field

		app_data_path = self.app_data_path

		try:
			vault_exists = io.vault_exists_for_gui(app_data_path, name)
		except OSError as e:
			name_field.error_widget.text = "Something went wrong, check log"
			name_field.error = True

			log(
				message="Something went wrong while creating vault",
				error=e
			)
			return

		if vault_exists:
			name_field.error_widget.text = "Vault already exists"
			name_field.error = True
			return

		if password != conf_password:
			confirm_password_field.error_widget.text = "Password does not match"
			confirm_password_field.error = True
			return

		try:
			app_data_path = self.app_data_path
			io.create_and_load_vault_for_gui(app_data_path, name, password)
			self.load_vaults()
			dialog.dismiss()

		except FileNotFoundError:
			name_field.error_widget.text = "Could not create vault file"
			name_field.error = True
		except PasswordRequirementsError as e:
			password_field.error_widget.text = f"Password does not meet the minimum requirements. Reason: {e.reason}"
			password_field.error = True
		except KeyLengthError:
			password_field.error_widget.text = "Password did not produce correct key length, contact developer"
			password_field.error = True
		except KeyDerivationError:
			password_field.error_widget.text = "Key derivation failed."
			password_field.error = True
		except (OverflowError, OSError) as e:
			if isinstance(e, OverflowError):
				name_field.error_widget.text = "Encryption failed"
			else:
				name_field.error_widget.text = "Something went wrong, check log"
			name_field.error = True

			log(
				message="Something went wrong while creating vault",
				error=e
			)

##	Open Vault Function	##

	def show_open_vault_dialog(self, instance: VaultEntry) -> None:
		login_dialog = LoginDialog(
			vault=instance.vault_name,
			login_callback=self.screen_manager.open_vault
		).open()
