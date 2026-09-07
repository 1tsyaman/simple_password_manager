from __future__ import annotations

import os
import copy
from collections.abc import Callable

import storage.io as io
from core.authenticate import generate_tag, is_authentic, encode_data
from core.types import config_t
from core.errors import (
	InvalidVaultFile,
	SettingsFileModifiedError,
	SettingsKeyNotSetError,
	log
)
from core.constants import (
	RELATIVE_CONFIG_PATH,
	SETTINGS_DICT_SECTIONS,
	PWD_GEN_SUBSECTIONS,
	SECURITY_SUBSECTIONS,
	OTHERS_SUBSECTIONS,
	HMAC_SUBSECTIONS,
	DEFAULT_SETTINGS
)

class Settings:
	"""
		@raises:
			- OSError
	"""
	def __init__(
		self,
		sync_callback	: Callable[[dict[str, dict]], None],
		settings		: dict[str, dict],
		key				: bytes,
		salt			: bytes
	):
		self.sync_callback	= sync_callback
		self.settings		= settings
		self._key			= key
		self._salt			= salt

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

	def set_key_salt_pair(
		self,
		key:	bytes,
		salt:	bytes
	):
		self._key	= key
		self._salt	= salt

	def get_pwd_gen_config(self) -> dict[str, config_t]:
		return self.settings["Password Generation"]

	def get_security_config(self) -> dict[str, config_t]:
		return self.settings["Security"]

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def sync_to_file(self):
		if not self._key_is_set():
			raise SettingsKeyNotSetError

		settings = self.get_hashed_settings()
		return self.sync_callback(settings)

	def get_hashed_settings(self) -> dict[str, dict]:
		settings = copy.deepcopy(self.settings)
		data = encode_data(settings)

		hash = generate_tag(
			data=data,
			key=self._key
		)

		settings["HMAC"] = {
			"Salt": 	f"{bytes.hex(self._salt)}",
			"Hash":		f"{bytes.hex(hash)}"
		}

		return settings

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
			- InvalidVaultFile
			- SettingsFileModifiedError
	"""
	@staticmethod
	def load_settings(
		settings		: dict[str, dict],
		key				: bytes,
		salt			: bytes,
		sync_callback	: Callable[[dict[str, dict]], None]
	) -> Settings:
		if not Settings.settings_dict_is_valid(settings):
			raise InvalidVaultFile

		hmac = settings.pop("HMAC")
		hash = bytes.fromhex(hmac["Hash"])
		data = encode_data(settings)

		if not is_authentic(data, key, hash):
			raise SettingsFileModifiedError

		return Settings(
			settings=settings,
			key=key,
			salt=salt,
			sync_callback=sync_callback
		)

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	@staticmethod
	def from_key(
		key				: bytes,
		salt			: bytes,
		sync_callback	: Callable[[dict[str, dict]], None],
		settings		: dict[str, dict] = DEFAULT_SETTINGS,
	) -> Settings:
		settings_obj = Settings(
			settings=settings,
			key=key,
			salt=salt,
			sync_callback=sync_callback
		)

		settings_obj.sync_to_file()
		return settings_obj

	@staticmethod
	def settings_dict_is_valid(settings: dict[str, dict]) -> bool:
		return 	_is_sublist(SETTINGS_DICT_SECTIONS,	list(settings.keys())) 							\
			and	_is_sublist(PWD_GEN_SUBSECTIONS,	list(settings["Password Generation"].keys()))	\
			and _is_sublist(SECURITY_SUBSECTIONS,	list(settings["Security"].keys()))				\
			and _is_sublist(OTHERS_SUBSECTIONS,		list(settings["Others"].keys()))				\
			and _is_sublist(HMAC_SUBSECTIONS,		list(settings["HMAC"].keys()))

	@staticmethod
	def get_config_path(app_data_path: str) -> str:
		path = os.path.join(app_data_path, RELATIVE_CONFIG_PATH)
		if not os.path.exists(path):
			io.create_path(path)

		return path

def _is_sublist(ls1: list, ls2: list):
	return all(elem in ls2 for elem in ls1)