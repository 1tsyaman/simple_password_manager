import traceback
from collections.abc import Callable
from threading import Thread

from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock		# for scheduling kivy jobs

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.appbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.appbar import MDActionTopAppBarButton
from kivymd.uix.progressindicator import MDCircularProgressIndicator

from gui.selection_screen import SelectionScreen
from gui.vault_entry import VaultEntry, VaultList, AccountEntry, AccountList
from gui.login import LoginDialog, NewVaultDialog, InputField, NewAccountDialog, ErrorDialog

import storage.io as io

from core.errors import (PasswordError, KeyLengthError, KeyDerivationError,
						 	VaultFormatError, CorruptedVaultError, PasswordRequirementsError,
							EntryExistsError)

def init_app():
	Builder.load_file("top_bar.kv")

class TopBar(MDTopAppBar):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.back_callback : Callable | None = None			# indirect on_release callback for the back button
		self.plus_callback : Callable | None = None

	# direct on_release callback for the back button
	def on_back(self, instance=None):
		print("clicked!")
		if self.back_callback is not None:
			self.back_callback()

	def on_plus(self, instance=None):
		if self.plus_callback is not None:
			self.plus_callback()

class NoAccountsLabel(MDLabel):
	pass

class NoVaultsLabel(MDLabel):
	pass


class SimplePasswordManagerApp(MDApp):
	def switch_screen(self, screen: str, on_exit: bool = False):
		if screen in ["selection", "vault"] \
			and (
					self.screen_manager.current != "vault"
					or self.vault_screen_can_switch(on_exit=on_exit)	# current = vault? -> check if we can exit
				):
				self.screen_manager.current = screen

	def vault_screen_can_switch(self, on_exit: bool = False):
		return self.force_exit_vault \
				or (not self.changes_made or self.sync_pwd_manager(on_exit=on_exit))	# changes made -> sync

	def back_to_selection(self):
		self.switch_screen("selection", on_exit=True)

	def refresh_selection_screen(self):
		top_bar : TopBar = self.top_bar
		back_button : MDActionTopAppBarButton = self.back_button

		# New vault button
		top_bar.plus_callback = self.show_new_vault_dialog

		# Disable back button
		top_bar.back_callback = None
		back_button.disabled = True
		back_button.opacity = 0

		self.load_vaults_to_screen()

	def refresh_vault_screen(self):
		top_bar : TopBar = self.top_bar
		back_button : MDActionTopAppBarButton = self.back_button

		self.force_exit_vault = False

		# New account button
		top_bar.plus_callback = self.show_add_account_dialog

		# Enable back button
		top_bar.back_callback = self.back_to_selection
		back_button.disabled = False
		back_button.opacity = 1


	def clear_vault_screen(self):
		# Cancel loading if we quit while loading wasn't finished
		if hasattr(self, "account_load_event"):
			self.account_load_event.cancel()

		self.vault_screen_box.clear_widgets()
		self.vault_screen_box.add_widget(NoAccountsLabel())

	def clear_selection_screen(self):
		self.selection_screen_box.clear_widgets()
		self.selection_screen_box.add_widget(NoVaultsLabel())

	def load_vaults_to_screen(self):
		# refresh vault list
		self.vaults = io.get_vault_list(self.app_data_path)

		if len(self.vaults) == 0:
			# Add no_vaults_label
			self.selection_screen_box.clear_widgets()
			self.selection_screen_box.add_widget(NoVaultsLabel())
			return

		vault_list : VaultList 				= VaultList()

		for vault in self.vaults:
			entry = VaultEntry(name=vault)
			entry.bind(on_release=self.show_open_vault_dialog)

			vault_list.add_vault(entry)

		container : BoxLayout = self.selection_screen_box
		container.clear_widgets()
		container.add_widget(vault_list)

	def load_vault_entries_to_screen(self, login_dialog: LoginDialog):
#		loading_indicator : MDCircularProgressIndicator = self.login_dialog.loading_indicator
		self.account_list : AccountList = AccountList()

		accounts = self.pwd_manager.get_website_username_list()
		self.number_accounts = len(accounts)		# store number of accounts
		self.account_iterator = iter(accounts)	# create an iterator
#		loading_indicator.active = True (no longer needed)

		if self.number_accounts == 0:
			self.vault_screen_box.clear_widgets()
			self.vault_screen_box.add_widget(NoAccountsLabel())

			self.login_dialog.dismiss()

			return self.switch_screen("vault")

		# Function signature:
		# 	Clock.schedule_interval(self, callback(self, dt: float) -> bool, intervall in sec)
		self.account_load_event = Clock.schedule_interval(self._load_account_batch, 0)

	def _load_account_batch(self, dt: float) -> bool:
		batch_size = min(10, self.number_accounts)
		done = False

		# Add accounts in batches of 10
		for _ in range(batch_size):
			try:
				website, username = next(self.account_iterator)

			# Whenever we're done
			except StopIteration:
				done = True
				break

			entry = AccountEntry(website=website, username=username)
			self.account_list.add_account(entry)

		# only switch the screen once, after one batch is added
		if self.screen_manager.current != "vault":
			container : BoxLayout = self.vault_screen_box
			container.clear_widgets()
			container.add_widget(self.account_list)

			self.login_dialog.dismiss()
			self.switch_screen("vault")

			# stop loading while transitioning screens
			return False

		# if done = True, we return False -> don't schedule again
		return not done	

	"""
		Resumes loading the entries after screen has loaded
	"""
	def _resume_loading_account_batch(self):
		if self.number_accounts != 0:
			self.account_load_event = Clock.schedule_interval(self._load_account_batch, 0)

	def show_add_account_dialog(self):
		self.new_account_dialog = NewAccountDialog(add_account_callback=self.add_account)
		self.new_account_dialog.open()

	# Bound to vault entries
	def show_open_vault_dialog(self, instance: VaultEntry) -> None:
		self.login_dialog = LoginDialog(vault=instance.vault_name, login_callback=self.open_vault)
		self.login_dialog.open()


	def add_account(self, dialog: NewAccountDialog, website: str, username: str, password: str, description: str):
		try:
			self.pwd_manager.add_entry(website=website, username=username, password=password, description=description)
		except EntryExistsError:
			username_field = dialog.username_field
			error_widget = username_field.error_widget

			error_widget.text = "website/username combination already exists"
			username_field.error = True
			return

		# Add account to list (without refreshing the whole list)
		entry = AccountEntry(website=website, username=username)
		self.account_list.add_account(entry)
		self.changes_made = True

		self.sync_thread = Thread(target=self.sync_pwd_manager, kwargs={"on_exit": False}, daemon=False)	# daemon=False -> program will not exit until thread returns
		self.sync_thread.start()

		dialog.dismiss()

	def sync_pwd_manager(self, on_exit: bool = False) -> bool:
		try:
			self.pwd_manager.encrypt()
			self.changes_made = False	# need to introduce locks here
			return True
		except FileNotFoundError as e:
			reason = ""
		except KeyLengthError:
			reason = ""
		except OverflowError:
			reason = ""
		except OSError:
			reason = ""

		kwargs = {
					"error_title": "Error: Changes not saved",
					"error_message": reason,
					"first_button_label": "Dismiss",
					"first_button_callback": lambda dialog: dialog.dismiss(),
				}
		if on_exit:
			kwargs["second_button_label"]		= "Exit anyways"
			kwargs["second_button_callback"]	= self.force_exist_vault_screen

		# because UI work should only happen on the main thread
		Clock.schedule_once(
			lambda dt: self.show_error_dialog(kwargs=kwargs),
			0
		)
		return False

	def show_error_dialog(self, kwargs: dict):
		self.error_dialog = ErrorDialog(**kwargs)
		self.error_dialog.open()

	def force_exist_vault_screen(self, dialog: ErrorDialog):
		dialog.dismiss()
		self.force_exit_vault = True
		self.switch_screen("selection", on_exit=True)

	def open_vault(self, login_dialog: LoginDialog, vault_name: str, password: str):
		password_field : InputField = login_dialog.password_field 
		error_widget = password_field.error_widget

		try:
			self.pwd_manager = io.load_vault_for_gui(self.app_data_path, vault_name, password)
			self.load_vault_entries_to_screen(login_dialog=login_dialog)
			self.changes_made = False

		except PasswordError:
			error_widget.text = "Incorrect Password"
			password_field.error = True
		except FileNotFoundError:
			error_widget.text = f"Vault path not valid"
			password_field.error = True
		except KeyLengthError:
			error_widget.text = "Derived key has incorrect length, contact developer"
			password_field.error = True
		except KeyDerivationError:
			error_widget.text = "Failed to derive key from password"
			password_field.error = True
		except VaultFormatError:
			error_widget.text = "Vault format incorrect"
			password_field.error = True
		except CorruptedVaultError:
			error_widget.text = "Incorrect password or corrupted vault"
			password_field.error = True
		except Exception as e:
			print(f"Something went wrong while opening the vault: {e}")
			traceback.print_exc()
			error_widget.text = "Something went wrong, check log"
			password_field.error = True


	def show_new_vault_dialog(self):
		self.new_vault_dialog = NewVaultDialog(create_vault_callback=self.create_vault)
		self.new_vault_dialog.open()

	def create_vault(self, dialog: NewVaultDialog, name: str, password: str, conf_password: str):
		name_field 				: InputField = dialog.name_field
		password_field			: InputField = dialog.password_field
		confirm_password_field	: InputField = dialog.confirm_password_field

		try:
			vault_exists = io.vault_exists_for_gui(self.app_data_path, name)
		except OSError as e:
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
			self.load_vaults_to_screen()
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
		# Top bar
		self.top_bar : TopBar							= self.root.ids.top_bar
		self.plus_button : MDActionTopAppBarButton 		= self.top_bar.ids.new_vault_button
		self.back_button : MDActionTopAppBarButton		= self.top_bar.ids.back_button

		self.back_button.bind(on_release=self.top_bar.on_back)
		self.plus_button.bind(on_release=self.top_bar.on_plus)

		# Screen manager
		self.screen_manager : ScreenManager 			= self.root.ids.screen_manager

		# Selection screen
		self.selection_screen: MDScreen					= self.screen_manager.get_screen("selection")
		self.selection_screen_box : BoxLayout			= self.selection_screen.ids.selection_screen_box

		# Vault screen
		self.vault_screen: MDScreen						= self.screen_manager.get_screen("vault")
		self.vault_screen_box : BoxLayout				= self.vault_screen.ids.vault_screen_box
		self.force_exit_vault = False
		self.changes_made = False

		self.app_data_path = str(io.get_app_data_path())

		# init app
		self.refresh_selection_screen()

	# Should return the main widget, the selection screen in this case.
	def build(self):
		# Init top bar
		init_app()
		return Builder.load_file("main.kv")

if __name__ == "__main__":
	SimplePasswordManagerApp().run()