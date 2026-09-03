from typing import TYPE_CHECKING

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout

from gui.widgets.top_bar import SettingsScreenTopBar
from gui.widgets.settings_screen.settings_menu import SettingsMenu

from core.pwd_manager import PwdManager

# to avoid cicular import issues
if TYPE_CHECKING:
	from gui.screens.screen_manager import AppScreenManager

SETTINGS = {
	"Password Generation": {
		"special_chars":		"!\"#$%&'()*+,-./:<=>?@[\\]^_`{|}~",
		"password_length":		24,
		"use_uppercase":		True,
		"use_lowercase":		True,
		"use_digits":			True,
		"use_special":			True
	},

	"Security":	{
		"timeout_duration":		60,
		"lock_on_minimize":		True,
		"clipboard_timeout":	30,
		"show_passwords":		True
	},

	"Others": {
		"theme":				"Light"
	}
}

NUMERIC_RANGES = {
	"password_length":		(8, 128),
	"timeout_duration":		(10, 600),
	"clipboard_timeout":	(5, 120),
}

class SettingsScreen(MDScreen):
	def __init__(
		self,
		app_data_path	: str,
		screen_manager	: "AppScreenManager",	# forward reference for type checking
		pwd_manager		: PwdManager,
		*args,
		**kwargs
	):
		self.app_data_path	= app_data_path
		self.screen_manager	= screen_manager
		self.pwd_manager	= pwd_manager

		self.vault_name	= ""	# is set by the screen manager

		self.settings= SETTINGS	# TODO: Actually extract that from the pwd_manager

		self.main_container = MDBoxLayout()		# contains the account_list widget

		self.main_container.add_widget(
			SettingsMenu(
				settings=self.settings,
				numeric_ranges=NUMERIC_RANGES,
				change_callback=self.update_settings
			)
		)

		app = MDApp.get_running_app()
		assert app is not None

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

	def update_settings(
		self,
		key: str,
		value: object
	):
		for section in self.settings:
			for setting in section:
				if key == setting:
					self.settings[section][setting] = value
