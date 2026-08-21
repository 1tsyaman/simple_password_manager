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


class SimplePasswordManagerApp(MDApp):

	def back_to_selection(self):
		self.switch_screen("selection", on_exit=True)

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
		return Builder.load_file("main.kv")

if __name__ == "__main__":
	SimplePasswordManagerApp().run()