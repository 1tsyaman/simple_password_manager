from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager

from kivymd.app import MDApp
from kivymd.uix.appbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.appbar import MDActionTopAppBarButton

from gui.selection_screen import SelectionScreen
from gui.vault_entry import VaultEntry, VaultList
from gui.login import LoginDialog, NewVaultDialog, InputField

import storage.io as io

from core.errors import (PasswordError, KeyLengthError, KeyDerivationError,
						 	VaultFormatError, CorruptedVaultError, PasswordRequirementsError)


def init_app():
	Builder.load_file("top_bar.kv")

class TopBar(MDTopAppBar):
	pass


class SimplePasswordManagerApp(MDApp):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.app_data_path = str(io.get_app_data_path())
		self.vaults = io.get_vault_list(self.app_data_path)

	def load_vault_entries(self):
		if len(self.vaults) == 0:
			return

		screen_manager : ScreenManager 		= self.root.ids.screen_manager
		old_selection_screen : MDScreen 	= screen_manager.get_screen("selection")
		vault_list : VaultList 				= VaultList()

		for vault in self.vaults:
			entry = VaultEntry(name=vault)
			entry.bind(on_release=self.show_open_vault_dialog)

			vault_list.add_vault(entry)

		new_selection_screen = SelectionScreen(name="selection")
		new_selection_screen.add_widget(vault_list)

		screen_manager.remove_widget(old_selection_screen)
		screen_manager.add_widget(new_selection_screen)


	# Bound to vault entries
	def show_open_vault_dialog(self, instance: VaultEntry) -> None:
		self.login_dialog = LoginDialog(vault=instance.vault_name, callback=self.open_vault)
		self.login_dialog.open()

	def open_vault(self, login_dialog: LoginDialog, vault_name: str, password: str) -> bool:
		error_widget = login_dialog.password_field.error_widget
		try:
			pwd_manager = io.load_vault_for_gui(self.app_data_path, vault_name, password)
			return True

		except PasswordError:
			error_widget.text = "Incorrect Password"
		except FileNotFoundError:
			error_widget.text = f"Vault path not valid"
		except KeyLengthError:
			error_widget.text = "Derived key has incorrect length, contact developer"
		except KeyDerivationError:
			error_widget.text = "Failed to derive key from password"
		except VaultFormatError:
			error_widget.text = "Vault format incorrect"
		except CorruptedVaultError:
			error_widget.text = "Incorrect password or corrupted vault"
		except Exception as e:
			print(f"Something went wrong while opening the vault: {e}")
			error_widget.text = "Something went wrong, check log"
		
		return False

	def show_new_vault_dialog(self, instance: MDActionTopAppBarButton):
		self.new_vault_dialog = NewVaultDialog(callback=self.create_vault)
		self.new_vault_dialog.open()

	def create_vault(self, dialog: NewVaultDialog, name: str, password: str, conf_password: str):
		name_field 				: InputField = dialog.name_field
		password_field			: InputField = dialog.password_field
		confirm_password_field	: InputField = dialog.confirm_password_field

		try:
			vault_exists = io.vault_exists_for_gui(self.app_data_path, name)
		except OSError:
			print(f"Something went wrong while creating vault: {e}")
			name_field.error_widget.text = "Something went wrong, check log"
			name_field.error = True

			return False

		if vault_exists:
			name_field.error_widget.text = "Vault already exists"
			name_field.error = True

			return False

		if password != conf_password:
			confirm_password_field.error_widget.text = "Password does not match"
			confirm_password_field.error = True

			return False

		try:
			io.create_and_load_vault_for_gui(self.app_data_path, name, password)
			self.load_vault_entries()
			return True

		except FileNotFoundError:
			name_field.error_widget.text = "Could not create vault file"
			name_field.error = True
		except PasswordRequirementsError as e:
			password_field.error_widget.text = e.reason
			password_field.error = True
		except KeyLengthError:
			password_field.error_widget.text = "Password did not produce correct key length, contact developer"
			password_field.error = True
		except KeyDerivationError:
			password_field.error_widget.text = "Key derivation failed."
			password_field.error = True
		except OverflowError as e:
			print(f"Something went wrong while creating vault: {e}")
			name_field.error_widget.text = "Encryption failed"
			name_field.error = True
		except OSError as e:
			print(f"Something went wrong while creating vault: {e}")
			name_field.error_widget.text = "Something went wrong, check log"
			name_field.error = True

		return False

	def on_start(self):
		self.load_vault_entries()
		top_bar : TopBar = self.root.ids.top_bar

		# bind new vault button
		new_vault_button : MDActionTopAppBarButton = top_bar.ids.new_vault_button
		new_vault_button.bind(on_release=self.show_new_vault_dialog)


	# Should return the main widget, the selection screen in this case.
	def build(self):
		# Init top bar
		init_app()
		return Builder.load_file("main.kv")

if __name__ == "__main__":
	SimplePasswordManagerApp().run()