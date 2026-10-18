import os
from pathlib import Path
from threading import RLock	# Allows the thread that acquired it first to aquire it again
from typing import Any
from datetime import datetime, timezone
from copy import deepcopy

from storage.constants import VAULT_ENDING
from core.password_manager.encrypt import get_salt_from_vault, atomic_write
from core.password_manager.keys import derive_master_key, derive_subkey, get_random_salt
from core.password_manager.pwd_manager import PwdManager
from core.settings.settings import Settings
from core.password_manager.passwords import password_satisfies_explicit_conditions
from core.sync.sync_manager import SyncManager
from core.sync.sync_callbacks import SyncCallbacks
from core.etc.authenticate import encode_data, is_authentic, generate_tag
from core.etc.errors import (
	PasswordError,
	PasswordRequirementsError,
	InvalidVaultFile,
	NoVaultFileError,
	InvalidJSONError,
	SettingsFieldModifiedError,
	MetadataFieldModifiedError,
	log,
)

import storage.io as io

"""
	Vault file structure:
	{
		"Vault": {
			"salt"				: hex,
			"nonce"				: hex,
			"ciphertext"		: hex,
			"associated_data"	: hex
		},

		"Settings": {
			"Password Generation": {
				"special_chars"		: string,
				"password_length"	: int,
				"use_uppercase"		: bool,
				"use_digits"		: bool,
				"use_special"		: bool
			},

			"Security": {
				"timeout_duration"	: int,
				"lock_on_minimize"	: bool
			},

			"Others": {
				"theme"				: string
			}
		},

		"Metadata": {
			"id"				: uuid,
			"version"			: uuid,
			"last_modified"		: datetime
		},

		"HMAC": {
			"Salt"				: hex,
			"Settings Hash"		: hex,
			"Metadata Hash"		: hex
		}
	}
"""
class VaultSession:
	vault_path	: str
	vault_key	: bytes
	auth_key	: bytes
	salt		: bytes
	json		: dict[str, dict]

	# Guards the reads/writes on the vault file and in-memory keys/salt
	lock		: RLock

	VAULT_FILE_KEYS = ["Vault", "Settings", "Metadata", "HMAC"]

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- VaultFormatError
			- PasswordRequirementsError
			- PasswordError
			- MetadataFieldModifiedError
			- OSError
	"""
	def __init__(
		self,
		app_data_path	: str,
		vault_name		: str,
		password		: str,
		new_vault		: bool = False
	) -> None:
		satisfies, reason = password_satisfies_explicit_conditions(password)

		if not satisfies:
			if new_vault:
				raise PasswordRequirementsError(
					reason=reason
				)
			else:
				raise PasswordError

		self.vault_path	= os.path.join(app_data_path, vault_name + VAULT_ENDING)

		self.json = {
			"Vault"		: {},
			"Settings"	: {},
			"Metadata"	: self._get_fresh_metadata(),
			"HMAC"		: {
				"Salt"			: bytes(0).hex(),
				"Settings Hash"	: bytes(0).hex(),
				"Metadata Hash"	: bytes(0).hex()
			},
		}

		if new_vault:
			# Initialize file
			io.create_path(self.vault_path)
			atomic_write(self.json, Path(self.vault_path), indent=4)
			self.salt = get_random_salt()
		else:
			self.salt = get_salt_from_vault(self.vault_path)

		self.json["HMAC"]["Salt"] = self.salt.hex()

		# derrive master key
		_, master_key = derive_master_key(
			pwd=password,
			salt=self.salt
		)

		self.vault_key	= self._derive_vault_key(master_key)
		self.auth_key 	= self._derive_auth_key(master_key)
		self.lock 		= RLock()

		if not new_vault:
			# Defered until auth_key is derived
			if self._vault_has_old_format():
				self._convert_vault_to_new_format()

			# Metadata hash check
			self.json = self.read_json()

			metadata	= deepcopy(self.json["Metadata"])
			hmac		= self.json["HMAC"]["Metadata Hash"]

			if not self._dict_is_authentic(
				dict_obj=metadata,
				recorded_hmac=hmac
			):
				raise MetadataFieldModifiedError

	"""
		@raises:
			- PasswordRequirementsError(reason)
			- KeyLengthError
			- KeyDerivationError
			- OverflowError
			- OSError
	"""
	def modify_master_password(
		self,
		password	: str,
		pwd_manager	: PwdManager,
		settings	: Settings
	):
		satisfies, reason = password_satisfies_explicit_conditions(password)

		if not satisfies:
			raise PasswordRequirementsError(
				reason=reason
			)

		salt, master_key = derive_master_key(password)

		with self.lock:
			old_salt		= self.salt
			old_vault_key	= self.vault_key
			old_auth_key	= self.auth_key

			vault_key		= self._derive_vault_key(master_key)
			auth_key		= self._derive_auth_key(master_key)

			self._set_salt_and_keys(salt, vault_key, auth_key)
			pwd_manager.set_key_salt_pair(
				key=vault_key,
				salt=salt
			)

			try:
				self.sync(
					pwd_manager=pwd_manager,
					settings=settings
				)
			except Exception as e:
				log(
					message="Something went wrong while trying to sync with the new key.",
					error=e
				)

				# Restore old values
				self._set_salt_and_keys(old_salt, old_vault_key, old_auth_key)
				pwd_manager.set_key_salt_pair(
					key=old_vault_key,
					salt=old_salt
				)
				raise

	def set_vault_name(
		self,
		vault_name: str
	):
		with self.lock:
			app_data_path = os.path.dirname(self.vault_path)
			self.vault_path = os.path.join(
				app_data_path,
				vault_name + VAULT_ENDING
			)

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- VaultFormatError
			- CorruptedVaultError
			- InconsistentVaultState
			- OSError
	"""
	def get_pwd_manager(self) -> PwdManager:
		with self.lock:
			try:
				self.json = self.read_json()

			except FileNotFoundError:
				raise NoVaultFileError
			except InvalidJSONError:
				raise InvalidVaultFile
			except OSError as e:
				log(
					message=f"Failed to open vault file {self.vault_path}",
					error=e
				)
				raise

			if not self._is_valid_vault_file():
				raise InvalidVaultFile

			vault		= self.json["Vault"]
			vault_key	= self.vault_key
			salt		= self.salt

		return PwdManager.from_encrypted_file_key(
			vault=vault,
			key=vault_key,
			salt=salt,
			sync_callback=self.sync_vault,
			lock=self.lock,
		)

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- OSError
	"""
	def create_pwd_manager(self) -> PwdManager:
		with self.lock:
			vault_key	= self.vault_key
			salt		= self.salt

		return PwdManager.pwd_manager_from_key(
			key=vault_key,
			salt=salt,
			sync_callback=self.sync_vault,
			lock=self.lock,
		)

	"""
		@raises:
			- NoVaultFileError
			- InvalidVaultFile
			- SettingsFieldModifiedError
			- OSError
	"""
	def get_settings(self) -> Settings:
		with self.lock:
			try:
				self.json = self.read_json()
			except FileNotFoundError:
				raise NoVaultFileError
			except InvalidJSONError:
				raise InvalidVaultFile
			except OSError as e:
				log(
					message=f"Failed to open vault file {self.vault_path}",
					error=e
				)
				raise

			if not self._is_valid_vault_file():
				raise InvalidVaultFile

			settings	= self.json["Settings"]
			hmac		= self.json["HMAC"]["Settings Hash"]

			if not self._dict_is_authentic(
				dict_obj=settings,
				recorded_hmac=hmac
			):
				raise SettingsFieldModifiedError

		return Settings.load_settings(
			settings=settings,
			sync_callback=self.sync_settings,
		)

	"""
		@raises:
			- FileNotFoundError
			- InvalidJSONError
			- OSError
	"""
	def sync_settings(
		self,
		settings: dict[str, dict]	# hashed dict
	):
		with self.lock:
			try:
				self.json = self.read_json()
			except FileNotFoundError:
				raise NoVaultFileError
			except InvalidJSONError:
				raise InvalidVaultFile
			except OSError as e:
				log(
					message=f"Failed to open vault file {self.vault_path}",
					error=e
				)
				raise

			self.json["Settings"]	= settings

			settings_hash			= self.get_hash(settings)
			hmac					= self.json["HMAC"]
			hmac["Settings Hash"]	= settings_hash.hex()

			self._update_and_hash_metadata()

			atomic_write(self.json, Path(self.vault_path), indent=4)

	"""
		@raises:
			- FileNotFoundError
			- InvalidJSONError
			- OSError
	"""
	def sync_vault(
		self,
		vault: dict[str, str]	# encrypted dict
	):
		with self.lock:
			try:
				self.json = self.read_json()
			except FileNotFoundError:
				raise NoVaultFileError
			except InvalidJSONError:
				raise InvalidVaultFile
			except OSError as e:
				log(
					message=f"Failed to open vault file {self.vault_path}",
					error=e
				)
				raise

			self.json["Vault"]		= vault
			hmac					= self.json["HMAC"]
			hmac["Salt"]			= self.salt.hex()

			self._update_and_hash_metadata()

			atomic_write(self.json, Path(self.vault_path), indent=4)

	def sync(
		self,
		pwd_manager	: PwdManager,
		settings	: Settings
	):
		with self.lock:
			encrypted_vault = pwd_manager.get_encrypted_vault()
			settings_dict = settings.get_settings_dict_copy()
			settings_hash = self.get_hash(settings_dict)

			self.json["Vault"]		= encrypted_vault
			self.json["Settings"]	= settings_dict

			hmac					= self.json["HMAC"]
			hmac["Salt"]			= self.salt.hex()
			hmac["Settings Hash"]	= settings_hash.hex()

			self._update_and_hash_metadata()

			atomic_write(self.json, Path(self.vault_path), indent=4)

	"""
		@raises:
			- FileNotFoundError
			- InvalidJSONError
			- OSError
	"""
	def read_json(self) -> dict[str, dict]:
		return self._read_json(self.vault_path)

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def create_settings(self) -> Settings:
		return Settings.create(
			sync_callback=self.sync_settings,
		)

	def get_hash(
		self,
		data: Any
	) -> bytes:
		"""
			Uses self.auth_key to hmac the provided data
		"""
		data_bytes = encode_data(data)

		with self.lock:
			auth_key = self.auth_key

		return generate_tag(
			data=data_bytes,
			key=auth_key
		)

	def _dict_is_authentic(
		self,
		dict_obj		: dict[str, str],
		recorded_hmac	: str
	) -> bool:
		"""
			Requires self.lock be acquired **before** getting recorded tag (and throughout this call)
		"""
		auth_key = self.auth_key
		data_bytes = encode_data(dict_obj)

		return is_authentic(
			data=data_bytes,
			key=auth_key,
			tag=bytes.fromhex(recorded_hmac)
		)

	def _set_salt_and_keys(
		self,
		salt		: bytes,
		vault_key	: bytes,
		auth_key	: bytes
	):
		with self.lock:
			self.salt		= salt
			self.vault_key	= vault_key
			self.auth_key	= auth_key

	def _is_valid_vault_file(self) -> bool:
		keys = set(self.json.keys())
		return keys == {*self.VAULT_FILE_KEYS}		\
				and "Settings Hash" in self.json["HMAC"]

	"""
		Checks if vault has old format (pre google-drive feature)

		@raises:
			- InvalidVaultFile
	"""
	def _vault_has_old_format(self) -> bool:
		try:
			vault_file = self._read_json(self.vault_path)
		except (
			FileNotFoundError,
			OSError,
			InvalidJSONError
		) as e:
			if isinstance(e, FileNotFoundError):
				error_message = "Vault file does not exist."
			elif isinstance(e, InvalidJSONError):
				error_message = "Vault file is not a valid JSON"
			else:
				error_message = "Loading the vault caused an OSError."
		
			log(
				message=f"Failed while checking vault format: {error_message}",
				error=e
			)
			raise InvalidVaultFile
		
		keys = set(vault_file.keys())

		return keys == {"Vault", "Settings"}


	"""
		Moves hmac out of the settings field

		@raises:
			- InvalidVaultFile
			- KeyError
	"""
	def _convert_vault_to_new_format(self):
		try:
			vault_file = self._read_json(self.vault_path)
		except (
			FileNotFoundError,
			OSError,
			InvalidJSONError
		) as e:
			if isinstance(e, FileNotFoundError):
				error_message = "Vault file does not exist."
			elif isinstance(e, InvalidJSONError):
				error_message = "Vault file is not a valid JSON"
			else:
				error_message = "Loading the vault caused an OSError."
		
			log(
				message=f"Failed while reading vault file: {error_message}",
				error=e
			)
			raise InvalidVaultFile

		settings				= vault_file["Settings"]
		hmac : dict[str, str]	= settings.pop("HMAC")
		settings_hash			= hmac.pop("Hash")
		hmac["Settings Hash"]	= settings_hash

		metadata		= self._get_fresh_metadata()
		metadata_hash	= self.get_hash(metadata)
		hmac["Metadata Hash"] = metadata_hash.hex()

		new_vault = {
			"Vault"		: vault_file["Vault"],
			"Settings"	: settings,
			"Metadata"	: metadata,
			"HMAC"		: hmac
		}
		self.json = new_vault

		atomic_write(new_vault, Path(self.vault_path), indent=4)

	def _get_fresh_id(self) -> str:
		return SyncManager.get_fresh_version()

	def _get_fresh_version(self) -> str:
		return SyncManager.get_fresh_version()

	def _get_fresh_metadata(self) -> dict[str, str]:
		return {
			"id"			: self._get_fresh_id(),
			"version"		: self._get_fresh_version(),
			"last_modified"	: self._get_current_time_str()
		}

	def _update_and_hash_metadata(self) -> None:
		with self.lock:
			self.json["Metadata"]["version"]		= self._get_fresh_version()
			self.json["Metadata"]["last_modified"]	= self._get_current_time_str()

			metadata_copy							= deepcopy(self.json["Metadata"])
			self.json["HMAC"]["Metadata Hash"]		= self.get_hash(metadata_copy).hex()

	"""
		@raises:
			- InvalidVaultFile
	"""
	@staticmethod
	def get_theme_from_vault_file(
		app_data_path	: str,
		vault_name		: str
	) -> str:
		vault_path	= os.path.join(app_data_path, vault_name + VAULT_ENDING)
		try:
			json = VaultSession._read_json(vault_path)
			return Settings.get_theme_from_json(json)
		except:
			raise InvalidVaultFile

	@staticmethod
	def _get_current_time_str() -> str:
		return datetime.now(timezone.utc).isoformat()

	@staticmethod
	def _get_datetime_from_str(time: str) -> datetime:
		return datetime.fromisoformat(time)

	@staticmethod
	def _derive_vault_key(master_key: bytes) -> bytes:
		return derive_subkey(
			master_key=master_key,
			purpose="vault-encryption"
		)

	@staticmethod
	def _derive_auth_key(master_key: bytes) -> bytes:
		return derive_subkey(
			master_key=master_key,
			purpose="settings-auth"
		)

	"""
		@raises:
			- FileNotFoundError
			- InvalidJSONError
			- OSError
	"""
	@staticmethod
	def _read_json(path: str) -> dict[str, dict]:
		return io.load_json(path)
