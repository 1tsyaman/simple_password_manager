from kivymd.app import MDApp
from kivymd.uix.widget import Widget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.transition import MDSharedAxisTransition
from kivymd.uix.boxlayout import MDBoxLayout

from gui.screens.welcome_screen import WelcomeScreen
from gui.screens.vault_screen import VaultScreen
from gui.screens.settings_screen import SettingsScreen
from gui.dialogs.selection_screen.login_dialog import LoginDialog
from gui.dialogs.selection_screen.new_vault_dialog import NewVaultDialog
from gui.dialogs.error_dialog import ErrorDialog
from gui.widgets.input_field import InputField
from gui.widgets.vault_screen.search_bar import SearchBar

from core.pwd_manager import PwdManager
from core.settings import Settings
from core.errors import (
	PasswordError,
	KeyLengthError,
	KeyDerivationError,
	VaultFormatError,
	CorruptedVaultError,
	NoSettingsFileError,
	InvalidSettingsFile,
	SettingsFileModifiedError,
	SettingsLoadError,
	log
)

import storage.io as io

class AppScreenManager(MDScreenManager):
	def __init__(
		self,
		app: MDApp,
		app_name: str,
		phone_screen: MDScreen,
		top_container: MDBoxLayout,
		pwd_manager: PwdManager,
		*args,
		**kwargs
	):
		self.app_name = app_name
		self.app = app
		self.app_data_path = str(io.get_app_data_path())
		self.top_container = top_container

		self.welcome_screen = WelcomeScreen(
			app_data_path=self.app_data_path,
			app_name=self.app_name,
			screen_manager=self
		)
		self.vault_screen = VaultScreen(
			app_data_path=self.app_data_path,
			phone_screen=phone_screen,
			screen_manager=self,
			pwd_manager=pwd_manager,
		)
		self.settings_screen = SettingsScreen(
			app_data_path=self.app_data_path,
			screen_manager=self,
			pwd_manager=pwd_manager,
			app=self.app,
		)

		# Signal that this is the first time we queue the selection screen
		self.welcome_screen.prompt_login = True

		"""
			This flag is set only when a vault is imported
			After a vault is imported, welcome_screen.refresh is called and
				welcome_screen.prompt_login is set -> if self.create_settings
				is also set, the current vault is a new (imported)
				vault and we create new settings file for it
		"""
		self.create_settings = False

		super().__init__(
			self.welcome_screen,
			self.vault_screen,
			self.settings_screen,
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
	def open_new_vault(
		self,
		dialog: NewVaultDialog,
		vault_name: str,
		password: str
	):
		try:
			app_data_path = self.app_data_path
			pwd_manager = io.load_vault_for_gui(app_data_path, vault_name, password)
			self.vault_screen.settings = Settings.load_settings(
				app_data_path=self.app_data_path,
				password=password
			)
			self.vault_screen.pwd_manager = pwd_manager
			self.vault_screen.login_dialog = dialog
			self.switch_screen(
				"vault",
				vault_name=vault_name
			)
			return

		except:
			self.show_error_dialog(
				error_title="Error",
				error_message="Failed to open newly created vault"
			)

	"""
		Opens the vault and triggers screen change on success.
		Emits error on failure directly into the login dialog.
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

			try:
				settings = self._load_settings(password)
			except SettingsLoadError:
				# Error dialog is shown by self._load_settings
				return

			pwd_gen_config = settings.get_pwd_gen_config()
			pwd_manager.set_pwd_gen_config(pwd_gen_config)

			self.vault_screen.settings = settings
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
		screen		: str,
		vault_name	: str ="",
		pwd_manager	: PwdManager | None = None,
		settings	: Settings | None = None
	):
		if (screen in ["welcome", "vault", "settings"] \
			and (
					self.current != "vault"
					or self.vault_screen_can_switch()	# current = vault? -> check if we can exit
			)
		):
			return self._switch_screen(screen, vault_name, pwd_manager, settings)

	def vault_screen_can_switch(self):
		vault_screen = self.vault_screen

		return vault_screen.force_exit_vault \
				or (vault_screen.sync_pwd_manager(on_exit=True))

	def force_exist_vault_screen(self, dialog: ErrorDialog):
		dialog.dismiss()
		self.vault_screen.force_exit_vault = True
		self.switch_screen("welcome")

	def back_to_welcome_screen(self):
		self.switch_screen("welcome")

	def back_to_vault(
		self,
		pwd_manager: PwdManager,
		vault_name	: str
	):
		self.vault_screen.pwd_manager = pwd_manager
		self.vault_screen.login_dialog = MDDialog()	# bogus dialog
		self.switch_screen(
			"vault",
			vault_name=vault_name
		)
		return

	def lock_vault(self):
		self._switch_screen("welcome")

	def exit_app(self):
		self.app.stop()

	"""
		kwargs:
			error_title: str,
			error_message: str,
			first_button_label: str = "dismiss",
			second_button_label: str = "",
			first_button_callback: Callable | None = None,
			second_button_callback: Callable | None = None,
	"""
	def show_error_dialog(
		self,
		**kwargs
	):
		self.error_dialog = ErrorDialog(**kwargs)
		self.error_dialog.open()

	def switch_top_bar(
		self,
		widget: Widget,
		padding: str = "0dp"
	):
		widget.size_hint = (1,1)

		# Detach search bar, if attached
		for child in self.top_container.children:
			if isinstance(child, SearchBar):
				child.detach()

		self.top_container.clear_widgets()
		self.top_container.add_widget(widget)
		self.top_container.padding = padding

	def _switch_screen(
		self,
		screen		: str,
		vault_name	: str = "",
		pwd_manager	: PwdManager | None = None,
		settings	: Settings | None = None,
		lock_vault	: bool = False,
	):
		attribute = f"{screen}_screen"

		try:
			screen_object = getattr(self, attribute)	# example: vault_screen
		except AttributeError:
			ErrorDialog(
				error_title="Error",
				error_message="Could not switch screens, check log.",
				first_button_callback=lambda *_: self.exit_app()		# if lock_vault flag is set
							if lock_vault else None						# 'Dismiss' closes the app
			).open()
			log(
				message=f"Attribute {attribute} is not associated with the screen manager option: Screen: {screen}."
			)

			return

		if screen in ["vault", "settings"]:
			screen_object.vault_name = vault_name

		if screen == "settings":
			screen_object.pwd_manager	= pwd_manager
			screen_object.settings_obj	= settings

		if self.current == "vault":
			self.app.close_all_dialogs()

		screen_object.top_bar = self.top_container
		self.current = screen

	"""
		@raises:
			- SettingsLoadError
	"""
	def _load_settings(
		self,
		password: str
	) -> Settings:
		if self.create_settings:
			# This vault is imported, create a fresh settings file for it
			settings = Settings.from_password(
				app_data_path=self.app_data_path,
				password=password
			)

			self.create_settings = False
			return settings

		error_message = ""
		try:
			return Settings.load_settings(
				app_data_path=self.app_data_path,
				password=password
			)

		except NoSettingsFileError:
			error_message = "Settings file was not found."
		except InvalidSettingsFile:
			error_message = "Settings file is invalid."
		except SettingsFileModifiedError:
			error_message = "Settings file was illegally modified."
		except OSError:
			self.show_error_dialog(
				error_title="Fatal error:",
				error_message="Failed to load settings, check log."
			)
			raise SettingsLoadError

		self.show_error_dialog(
			error_title="Error",
			error_message=f"{error_message} Loading default settings."
		)
		try:
			return Settings.from_password(
				app_data_path=self.app_data_path,
				password=password
			)
		except:
			self.show_error_dialog(
				error_title="Error",
				error_message="Failed to laod default settings."
			)
			raise SettingsLoadError
