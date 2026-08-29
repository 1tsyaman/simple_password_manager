from typing import TYPE_CHECKING

from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.appbar import MDActionTopAppBarButton

from gui.widgets.top_bar import TopBar
from gui.widgets.labels import NoVaultsLabel
from gui.widgets.input_field import InputField
from gui.widgets.vault_list import VaultEntry, VaultList
from gui.widgets.import_picker import ImportFilePicker
from gui.widgets.export_picker import ExportFilePicker
from gui.dialogs.login_dialog import LoginDialog
from gui.dialogs.new_vault_dialog import NewVaultDialog
from gui.dialogs.rename_vault_dialog import RenameVaultDialog
from gui.widgets.vault_context_menu import VaultContextMenu

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
		app_name: str,
		screen_manager: "AppScreenManager",	# forward reference for type checking
		*args,
		**kwargs
	):
		self.app_data_path = app_data_path
		self.app_name = app_name
		self.screen_manager = screen_manager

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
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
		top_bar = TopBar(
			title=self.app_name
		)
		import_button: MDActionTopAppBarButton = top_bar.import_vault_button

		top_bar.remove_back_button()

		# Enable import button
		top_bar.import_callback = self.show_import_vault_file_picker
		import_button.disabled = False
		import_button.opacity = 1

		# New vault button
		top_bar.plus_callback = self.show_new_vault_dialog

		# Import vault button
		top_bar.import_callback = self.show_import_vault_file_picker

		self.screen_manager.switch_top_bar(top_bar)

		self.load_vaults()

	def load_vaults(self):
		# refresh vault list
		app_data_path = self.app_data_path
		self.vaults = io.get_vault_list(app_data_path)

		if len(self.vaults) == 0:
			# Add no_vaults_label
			self.clear_widgets()
			self.add_widget(NoVaultsLabel())
			return

		vault_list = VaultList()

		for vault in self.vaults:
			entry = VaultEntry(
				name=vault,
				context_callback=self.show_vault_context_menu
			)
			entry.bind(on_release=self.show_open_vault_dialog)

			vault_list.add_vault(entry)

		self.clear_widgets()
		self.add_widget(vault_list)

	def on_back(self):
		self.screen_manager.exit_app()

	def on_leave(self, *args):
		self.clear()

	"""
		is called when leaving the screen
	"""
	def clear(self):
		self.clear_widgets()
		self.add_widget(NoVaultsLabel())

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

	def rename_vault(
		self,
		old_name: str,
		new_name: str
	):
		try:
			io.rename_vault(
				path=self.app_data_path,
				vault_name=old_name,
				new_vault_name=new_name
			)

			self.refresh()

		except (
			FileNotFoundError,
			FileExistsError,
			OSError,
		) as e:
			log(
				message=f"Something went wrong while renaming vault {old_name}.",
				error=e
			)

			self.screen_manager.show_error_dialog(
				error_title="Rename Error:",
				error_message="Failed to rename vault, check log"
			)

####	Open Dialog/Menu Methods	####

	def show_new_vault_dialog(self):
		NewVaultDialog(
			create_vault_callback=self.create_vault
		).open()

	def show_vault_context_menu(
		self,
		instance: VaultEntry,
		button: Widget
	):
		name = instance.vault_name
		VaultContextMenu(
			export_callback=lambda: self.show_export_vault_dialog(name),
			rename_callback=lambda: self.show_rename_vault_dialog(name),
			caller=button
		).open()

	def show_open_vault_dialog(self, instance: VaultEntry) -> None:
		LoginDialog(
			vault=instance.vault_name,
			login_callback=self.screen_manager.open_vault
		).open()

	def show_rename_vault_dialog(
		self,
		vault_name: str
	):
		RenameVaultDialog(
			vault_name=vault_name,
			rename_callback=self.rename_vault
		).open()

	def show_export_vault_dialog(
		self,
		vault_name: str
	):
		ExportFilePicker(
			app_data_path=self.app_data_path,
			vault_name=vault_name
		).open()

	def show_import_vault_file_picker(self):
		ImportFilePicker(
			app_data_path=self.app_data_path,
			refresh_callback=self.refresh
		).open()