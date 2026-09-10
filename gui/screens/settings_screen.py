from typing import TYPE_CHECKING
from collections.abc import Callable
from threading import Lock

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

from gui.widgets.top_bar import SettingsScreenTopBar
from gui.widgets.settings_screen.settings_menu import SettingsMenu

from core.pwd_manager import PwdManager, SPECIAL_CHARS
from core.settings import Settings
from core.types import config_t

# to avoid cicular import issues
if TYPE_CHECKING:
	from gui.main import SimplePasswordManagerApp
	from gui.screens.screen_manager import AppScreenManager

NUMERIC_RANGES = {
	"password_length":		(8, 128),
	"timeout_duration":		(10, 300)
}

class SettingsScreen(MDScreen):
	settings_obj	: Settings		# Set by screen_manager
	pwd_manager		: PwdManager 	# Set by screen_manager
	sync_callback	: Callable		# Set by screen_manager

	def __init__(
		self,
		app_data_path	: str,
		screen_manager	: "AppScreenManager",	# forward reference for type checking
		app				: "SimplePasswordManagerApp",
		vault_lock		: Lock,
		*args,
		**kwargs
	):
		self.app_data_path	= app_data_path
		self.screen_manager	= screen_manager
		self.app			= app
		self.vault_lock		= vault_lock

		self.vault_name	= ""	# is set by the screen manager

		self.main_container = MDBoxLayout()		# contains the account_list widget

		super().__init__(
			name="settings",
			md_bg_color=app.theme_cls.secondaryContainerColor,
			*args,
			**kwargs
		)

		self.add_widget(self.main_container)


	def on_pre_enter(self, *args):
		self.refresh()

	def refresh(self):
		top_bar = SettingsScreenTopBar(
			back_callback=lambda *_: self.screen_manager.back_to_vault(
										pwd_manager=self.pwd_manager,
										vault_name=self.vault_name
									)
		)

		self.screen_manager.switch_top_bar(top_bar)

		self.main_container.clear_widgets()
		self.main_container.add_widget(
			SettingsMenu(
				settings=self.settings_obj.settings,
				numeric_ranges=NUMERIC_RANGES,
				change_callback=self.update_settings,
				theme_callback=self.apply_theme,
				allowed_special_chars=SPECIAL_CHARS
			)
		)

	def update_settings(
		self,
		key: str,
		value: config_t
	):
		with self.vault_lock:
			self.settings_obj.set_settings_value(key, value)

	def apply_theme(
		self,
		theme: str
	):
		self.app.apply_theme(theme)


	def on_leave(self, *args):
		self.sync_callback()

		pwd_gen_config = self.settings_obj.get_pwd_gen_config()
		self.pwd_manager.set_pwd_gen_config(pwd_gen_config)

		with self.vault_lock:
			app_settings = self.settings_obj.get_security_config()

			timeout_duration = app_settings["timeout_duration"]
			lock_on_minimize = app_settings["lock_on_minimize"]

		assert isinstance(timeout_duration, int) and isinstance(lock_on_minimize, bool)

		self.app.set_timeout_duration(timeout_duration)
		self.app.set_lock_on_minimize(lock_on_minimize)