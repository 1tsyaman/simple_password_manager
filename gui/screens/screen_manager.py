from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.transition import MDSharedAxisTransition

from gui.screens.selection_screen import SelectionScreen
from gui.screens.vault_screen import VaultScreen
from gui.dialogs.login_dialog import LoginDialog
from gui.dialogs.error_dialog import ErrorDialog
from gui.widgets.input_field import InputField
from gui.widgets.top_bar import TopBar

from core.pwd_manager import PwdManager
from core.errors import (
	PasswordError,
	KeyLengthError,
	KeyDerivationError,
	VaultFormatError,
	CorruptedVaultError,
	log
)

import storage.io as io

class AppScreenManager(MDScreenManager):
	def __init__(
		self,
		top_bar: TopBar,
		pwd_manager: PwdManager,
		*args,
		**kwargs
	):
		self.app_data_path = str(io.get_app_data_path())

		self.top_bar = top_bar
		self.selection_screen = SelectionScreen(
			app_data_path=self.app_data_path,
			screen_manager=self,
			top_bar=top_bar
		)
		self.vault_screen = VaultScreen(
			app_data_path=self.app_data_path,
			screen_manager=self,
			pwd_manager=pwd_manager,
			top_bar=top_bar
		)

		super().__init__(
			self.selection_screen,
			self.vault_screen,
			transition=MDSharedAxisTransition(
				transition_axis="x",
			),
			*args,
			**kwargs
		)

	"""
		Opens the vault and triggers screen change on success.
		Emits error on failure.
	"""
	def open_vault(
		self,
		dialog: LoginDialog,
		vault_name: str,
		password: str
	):
		password_field : InputField = dialog.password_field 
		error_widget = password_field.error_widget
		error_message = ""

		try:
			app_data_path = self.app_data_path
			pwd_manager = io.load_vault_for_gui(app_data_path, vault_name, password)
			self.vault_screen.pwd_manager = pwd_manager
			self.vault_screen.login_dialog = dialog
			self.switch_screen(
				"vault",
				vault_name=vault_name
			)
			return

		except PasswordError:
			error_message = "Incorrect Password"
		except FileNotFoundError:
			error_message = "Vault path not valid"
		except KeyLengthError:
			error_message = "Derived key has incorrect length, contact developer"
		except KeyDerivationError:
			error_message = "Failed to derive key from password"
		except VaultFormatError:
			error_message = "Vault format incorrect"
		except CorruptedVaultError:
			error_message = "Incorrect password or corrupted vault"
		except Exception as e:
			error_message = "Something went wrong, check log"
			log(
				message="Something went wrong while opening the vault",
				error=e
			)

		error_widget.text = error_message
		password_field.error = True

	def switch_screen(
		self,
		screen: str,
		vault_name: str ="",
		on_exit: bool = False
	):
		if (screen in ["selection", "vault"] \
			and (
					self.current != "vault"
					or self.vault_screen_can_switch()	# current = vault? -> check if we can exit
			)
		):
			attribute = f"{screen}_screen"

			try:
				screen_object = getattr(self, attribute)	# example: vault_screen
			except AttributeError:
				ErrorDialog(
					error_title="Error",
					error_message="Could not switch screens, check log."
				).open()
				log(
					message=f"Attribute {attribute} is not associated with the screen manager option: Screen: {screen}."
				)

				return

			if screen == "vault":
				screen_object.vault_name = vault_name

			screen_object.top_bar = self.top_bar
			self.current = screen

	def vault_screen_can_switch(self):
		vault_screen = self.vault_screen

		return vault_screen.force_exit_vault \
				or (vault_screen.sync_pwd_manager(on_exit=True))

	def force_exist_vault_screen(self, dialog: ErrorDialog):
		dialog.dismiss()
		self.vault_screen.force_exit_vault = True
		self.switch_screen("selection", on_exit=True)

	def back_to_selection(self):
		self.switch_screen("selection", on_exit=True)

	def show_error_dialog(self, **kwargs):
		self.error_dialog = ErrorDialog(**kwargs)
		self.error_dialog.open()