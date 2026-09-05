from collections.abc import Callable

from kivy.metrics import dp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from gui.widgets.settings_screen.choice import ChoiceSetting
from gui.widgets.settings_screen.slider import SliderSetting
from gui.widgets.settings_screen.section import SettingSection
from gui.widgets.settings_screen.switch import SwitchSetting
from gui.widgets.settings_screen.text import TextSetting

from core.types import config_t

class SettingsMenu(MDScrollView):
	def __init__(
		self,
		settings				: dict,
		allowed_special_chars	: list[str],
		numeric_ranges			: dict[str, tuple[int, int]],
		change_callback			: Callable[[str, config_t], None] | None = None,
		**kwargs
	):
		super().__init__(
			do_scroll_x=False,
			do_scroll_y=True,
			**kwargs
		)

		self.settings				= settings
		self.numeric_ranges			= numeric_ranges
		self.change_callback		= change_callback
		self.allowed_special_chars	= allowed_special_chars

		self.content = MDBoxLayout(
			orientation="vertical",
			adaptive_height=True,
			padding=dp(16),
			spacing=dp(8)
		)

		self.add_widget(self.content)

		for section, values in settings.items():
			self._add_section(section)

			for key, value in values.items():
				self._add_setting(section, key, value)

	def _add_section(self, title: str):
		self.content.add_widget(
			SettingSection(
				title=title
			)
		)

	def _add_setting(
		self,
		section: str,
		key: str,
		value: config_t
	):
		title = key.replace("_", " ").capitalize()

		if isinstance(value, bool):
			self._add_switch(section, key, title, value)

		elif isinstance(value, int):
			minimum, maximum = self.numeric_ranges[key]

			self._add_number(
				section,
				key,
				title,
				value,
				minimum,
				maximum
			)

		elif key == "theme":
			self._add_choice(
				section,
				key,
				title,
				str(value),
				["Light", "Dark"]
			)

		else:
			self._add_text(section, key, title, str(value))

	def _add_switch(
		self,
		section: str,
		key: str,
		title: str,
		value: bool
	):
		self.content.add_widget(
			SwitchSetting(
				title=title,
				value=value,
				set_value_callback=lambda _, active: self._set_value(section, key, active),
			)
		)

	def _add_number(
		self,
		section: str,
		key: str,
		title: str,
		value: int,
		minimum: int,
		maximum: int
	):
		self.content.add_widget(
			SliderSetting(
				title=title,
				value=value,
				minimum=minimum,
				maximum=maximum,
				set_value_callback=lambda new_value: self._set_value(section, key, new_value)
			)
		)

	def _add_text(
		self,
		section: str,
		key: str,
		title: str,
		value: str
	):
		self.content.add_widget(
			TextSetting(
				title=title,
				value=value,
				set_value_callback=lambda text: self._set_value(section, key, text),
				text_cleanup_callback=self._get_clean_special_char_string
			)
		)

	def _add_choice(
		self,
		section: str,
		key: str,
		title: str,
		value: str,
		options: list[str]
	):
		self.content.add_widget(
			ChoiceSetting(
				title=title,
				value=value,
				options=options,
				set_value_callback=lambda value: self._set_value(section, key, value)
			)
		)

	def _set_value(
		self,
		section: str,
		key: str,
		value: config_t
	):
		self.settings[section][key] = value

		if self.change_callback is not None:
			self.change_callback(key, value)


	def _get_clean_special_char_string(
		self,
		special_chars: str
	) -> str:
		ls = list(
			dict.fromkeys(
				[char for char in special_chars if char in self.allowed_special_chars]
			)
		)

		res = ""
		for char in ls:
			res += char

		return res