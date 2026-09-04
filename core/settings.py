from __future__ import annotations

import os
import json
import copy
from pathlib import Path

import storage.io as io
from core.encrypt import __atomic_write as atomic_write
from core.authenticate import generate_tag, is_authentic
from core.keys import derive_key
from core.errors import (
	NoSettingsFileError,
	InvalidJSONError,
	InvalidSettingsFile,
	SettingsFileModifiedError,
	SettingsKeyNotSetError,
	log
)

RELATIVE_CONFIG_PATH = "config/settings.json"

SETTINGS_DICT_SECTIONS	= [
	"Password Generation",
	"Security",
	"Others",
	"HMAC"
]

PWD_GEN_SUBSECTIONS		= [
	"special_chars",
	"password_length",
	"use_uppercase",
	"use_lowercase",
	"use_digits",
	"use_special",
]
SECURITY_SUBSECTIONS	= [
	"timeout_duration",
	"lock_on_minimize",
	"clipboard_timeout",
	"show_passwords"
]
OTHERS_SUBSECTIONS		= [
	"theme"
]
HMAC_SUBSECTIONS		= [
	"Salt",
	"Hash"
]

DEFAULT_SETTINGS = {
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

class Settings:
	"""
		@raises:
			- OSError
	"""
	def __init__(
		self,
		app_data_path	: str,
		settings		: dict[str, dict],
		key				: bytes,
		salt			: bytes
	):
		self.config_path 	= self.get_config_path(app_data_path)
		self.settings		= settings
		self._key			= key
		self._salt			= salt

		self.sync_to_file()

	"""
		Does not sync to file, synchronization should be done explicitly
		This avoids having constant changes spamming writes to the file
	"""
	def set_settings_value(
		self,
		key:	str,
		value:	object
	):
		if key in PWD_GEN_SUBSECTIONS:
			section = "Password Generation"
		elif key in SECURITY_SUBSECTIONS:
			section = "Security"
		elif key in OTHERS_SUBSECTIONS:
			section = "Others"
		else:
			return

		self.settings[section][key] = value

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def sync_to_file(self):
		if not self._key_is_set():
			raise SettingsKeyNotSetError

		settings = copy.deepcopy(self.settings)

		data = self.encode_data(settings)

		hash = generate_tag(
			data=data,
			key=self._key
		)

		settings["HMAC"] = {
			"Salt": 	f"{bytes.hex(self._salt)}",
			"Hash":		f"{bytes.hex(hash)}"
		}

		atomic_write(settings, Path(self.config_path), indent=4)

	def set_key(
		self,
		password: str
	):
		self._salt, self._key = derive_key(password)

	"""
		Overwrites the ./config/settings.json file with an authenticated
			settings.json file containing the DEFAULT_SETTINGS

		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def reset_to_default_settings(self):
		if not self._key_is_set():
			raise SettingsKeyNotSetError

		self.settings = DEFAULT_SETTINGS
		self.sync_to_file()

	def _key_is_set(self) -> bool:
		return len(self._key) != 0 and len(self._salt) != 0

	"""
		@raises:
			- NoSettingsFileError
			- InvalidSettingsFile
			- SettingsFileModifiedError
			- OSError
	"""
	@staticmethod
	def load_settings(
		app_data_path	: str,
		password		: str,
	) -> Settings:
		config_path = Settings.get_config_path(app_data_path)

		try:
			settings = io.load_settings(config_path)
		except FileNotFoundError:
			raise NoSettingsFileError
		except OSError as e:
			log(
				message=f"Failed to open settings file {config_path}",
				error=e
			)
			raise
		except InvalidJSONError:
			raise InvalidSettingsFile

		if not Settings.settings_dict_is_valid(settings):
			raise InvalidSettingsFile

		hmac = settings.pop("HMAC")

		salt = bytes.fromhex(hmac["Salt"])
		hash = bytes.fromhex(hmac["Hash"])

		_, key = derive_key(
			pwd=password,
			salt=salt
		)

		data = Settings.encode_data(settings)

		if not is_authentic(data, key, hash):
			raise SettingsFileModifiedError

		return Settings(
			app_data_path=app_data_path,
			settings=settings,
			key=key,
			salt=salt
		)

	@staticmethod
	def from_password(
		app_data_path	: str,
		password		: str,
		settings		: dict[str, dict] = DEFAULT_SETTINGS,
	) -> Settings:
		salt, key = derive_key(password)

		return Settings(
			app_data_path=app_data_path,
			settings=settings,
			key=key,
			salt=salt
		)

	@staticmethod
	def encode_data(data: dict) -> bytes:
		return json.dumps(
			data,
			sort_keys=True,
			separators=(",", ":")
		).encode()

	@staticmethod
	def settings_dict_is_valid(settings: dict[str, dict]) -> bool:
		return 	_is_sublist(SETTINGS_DICT_SECTIONS,	list(settings.keys())) 							\
			and	_is_sublist(PWD_GEN_SUBSECTIONS,	list(settings["Password Generation"].keys()))	\
			and _is_sublist(SECURITY_SUBSECTIONS,	list(settings["Security"].keys()))				\
			and _is_sublist(OTHERS_SUBSECTIONS,		list(settings["Others"].keys()))				\
			and _is_sublist(HMAC_SUBSECTIONS,		list(settings["HMAC"].keys()))

	@staticmethod
	def get_config_path(app_data_path: str):
		return os.path.join(app_data_path, RELATIVE_CONFIG_PATH)


def _is_sublist(ls1: list, ls2: list):
	return all(elem in ls2 for elem in ls1)