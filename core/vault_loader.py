import os
from pathlib import Path

from storage.constants import VAULT_ENDING
from core.encrypt import get_salt_from_vault, __atomic_write
from core.keys import derive_master_key, derive_subkey, get_random_salt
from core.pwd_manager import PwdManager
from core.settings import Settings
from core.passwords import password_satisfies_explicit_conditions
from core.errors import (
	PasswordError,
	PasswordRequirementsError,
	InvalidVaultFile,
	NoVaultFileError,
	InvalidJSONError,
	log,
)

import storage.io as io

class VaultSession:
	vault_path	: str
	vault_key	: bytes
	auth_key	: bytes
	salt		: bytes
	json		: dict[str, dict]

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- VaultFormatError
			- PasswordRequirementsError
			- PasswordError
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

		self.json = {
			"Vault":	{},
			"Settings":	{},
		}

		self.vault_path	= os.path.join(app_data_path, vault_name + VAULT_ENDING)

		if new_vault:
			# Initialize file
			io.create_path(self.vault_path)
			__atomic_write(self.json, Path(self.vault_path), indent=4)
			self.salt = get_random_salt()
		else:
			self.salt = get_salt_from_vault(self.vault_path)

		# derrive master key
		_, master_key = derive_master_key(
			pwd=password,
			salt=self.salt
		)

		self.vault_key	= self._derive_vault_key(master_key)
		self.auth_key 	= self._derive_auth_key(master_key)


	"""
		@raises:
			- PasswordRequirementsError(reason)
			- FileNotFoundError(path) [OSError]
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

		self.salt, master_key = derive_master_key(password)

		self.vault_key	= self._derive_vault_key(master_key)
		self.auth_key	= self._derive_auth_key(master_key)

		pwd_manager.set_key_salt_pair(
			key=self.vault_key,
			salt=self.salt
		)

		settings.set_key_salt_pair(
			key=self.auth_key,
			salt=self.salt
		)

		self.sync(
			pwd_manager=pwd_manager,
			settings=settings
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

		if not "Vault" in self.json.keys():
			raise InvalidVaultFile

		vault = self.json["Vault"]

		return PwdManager.from_encrypted_file_key(
			vault=vault,
			key=self.vault_key,
			salt=self.salt,
			sync_callback=self.sync_vault
		)

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- OSError
	"""
	def create_pwd_manager(self) -> PwdManager:
		return PwdManager.pwd_manager_from_key(
			key=self.vault_key,
			salt=self.salt,
			sync_callback=self.sync_vault
		)

	"""
		@raises:
			- NoVaultFileError
			- InvalidVaultFile
			- SettingsFileModifiedError
			- OSError
	"""
	def get_settings(self) -> Settings:
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

		if not "Settings" in self.json.keys():
			raise InvalidVaultFile

		settings = self.json["Settings"]

		return Settings.load_settings(
			settings=settings,
			key=self.auth_key,
			salt=self.salt,
			sync_callback=self.sync_settings
		)

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def create_settings(self) -> Settings:
		return Settings.from_key(
			key=self.auth_key,
			salt=self.salt,
			sync_callback=self.sync_settings,
		)

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
	def sync_settings(
		self,
		settings: dict[str, dict]	# hashed dict
	):
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

		self.json["Settings"] = settings

		__atomic_write(self.json, Path(self.vault_path), indent=4)

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

		self.json["Vault"] = vault

		__atomic_write(self.json, Path(self.vault_path), indent=4)

	def sync(
		self,
		pwd_manager	: PwdManager,
		settings	: Settings
	):
		encrypted_vault = pwd_manager.get_encrypted_vault()
		hashed_settings = settings.get_hashed_settings()

		self.json["Vault"]		= encrypted_vault
		self.json["Settings"]	= hashed_settings

		__atomic_write(self.json, Path(self.vault_path), indent=4)

	"""
		@raises:
			- FileNotFoundError
			- InvalidJSONError
			- OSError
	"""
	def read_json(self) -> dict[str, dict]:
		return io.load_json(self.vault_path)