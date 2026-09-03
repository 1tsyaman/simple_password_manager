from typing import TYPE_CHECKING

from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.anchorlayout import MDAnchorLayout

from gui.dialogs.selection_screen.login_dialog import LoginDialog
from gui.dialogs.selection_screen.new_vault_dialog import NewVaultDialog

from gui.widgets.top_bar import TopBar
from gui.widgets.input_field import InputField
from gui.widgets.welcome_screen.import_picker import ImportFilePicker
from gui.widgets.welcome_screen.card_widgets import NoVaultWidget, OpenVaultWidget

import storage.io as io

from core.errors import (
	PasswordRequirementsError,
	KeyLengthError,
	KeyDerivationError,
	log
)

if TYPE_CHECKING:
	from gui.screens.screen_manager import AppScreenManager

class WelcomeScreen(MDScreen):
	def __init__(
		self,
		app_data_path	: str,
		app_name		: str,
		screen_manager	: "AppScreenManager",
		*args,
		**kwargs
	):
		self.app_data_path	= app_data_path
		self.app_name		= app_name
		self.screen_manager	= screen_manager

		self.main_container = MDAnchorLayout(
		    anchor_x="center",
		    anchor_y="center"
		)

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
			name="welcome",
			md_bg_color=app.theme_cls.secondaryContainerColor,
			*args,
			**kwargs
		)

		self.add_widget(
			self.main_container
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

		self.screen_manager.switch_top_bar(top_bar)

		self.load_vaults()

	def load_vaults(self):
		# refresh vault list
		app_data_path = self.app_data_path
		vault_list = io.get_vault_list(app_data_path)

		if len(vault_list) == 0:
			# Add no_vaults_label
			self.main_container.clear_widgets()
			self.main_container.add_widget(
				NoVaultWidget(
					create_callback=self.show_new_vault_dialog,
					import_callback=self.show_import_vault_file_picker
				)
			)

			self.on_start = False	# never true again while running
			return

		# Open first vault in the list
		vault = vault_list[0]

		self.main_container.clear_widgets()
		self.main_container.add_widget(
			OpenVaultWidget(
				open_callback=lambda *_: self.show_open_vault_dialog(vault)
			)
		)

		if self.on_start:
			self.on_start = False	# never true again while running
			Clock.schedule_once(
				lambda *_: self.show_open_vault_dialog(vault),
				0
			)

	def on_back(self):
		self.screen_manager.exit_app()

	def on_leave(self, *args):
		self.clear()

	"""
		is called when leaving the screen
	"""
	def clear(self):
		self.main_container.clear_widgets()

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

####	Open Dialog/Menu Methods	####

	def show_new_vault_dialog(self):
		NewVaultDialog(
			create_vault_callback=self.create_vault
		).open()

	def show_open_vault_dialog(self, vault_name: str) -> None:
		LoginDialog(
			vault=vault_name,
			login_callback=self.screen_manager.open_vault
		).open()

	def show_import_vault_file_picker(self):
		ImportFilePicker(
			app_data_path=self.app_data_path,
			on_finish_callback=self.refresh,
			type=".vault"
		).open()