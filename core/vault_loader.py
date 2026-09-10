import os
from pathlib import Path
from threading import RLock	# Allows the thread that acquired it first to aquire it again

from storage.constants import VAULT_ENDING
from core.encrypt import get_salt_from_vault, atomic_write
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

	# Guards the reads/writes on the vault file and in-memory keys/salt
	lock		: RLock

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
			atomic_write(self.json, Path(self.vault_path), indent=4)
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
		self.lock 		= RLock()


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
			settings.set_key_salt_pair(
				key=auth_key,
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
				settings.set_key_salt_pair(
					key=old_auth_key,
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

			if not "Vault" in self.json.keys():
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
			- SettingsFileModifiedError
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

			if not "Settings" in self.json.keys():
				raise InvalidVaultFile

			settings	= self.json["Settings"]
			auth_key	= self.auth_key
			salt		= self.salt

		return Settings.load_settings(
			settings=settings,
			key=auth_key,
			salt=salt,
			sync_callback=self.sync_settings,
			lock=self.lock,
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

			self.json["Settings"] = settings

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

			self.json["Vault"] = vault

			atomic_write(self.json, Path(self.vault_path), indent=4)

	def sync(
		self,
		pwd_manager	: PwdManager,
		settings	: Settings
	):
		with self.lock:
			encrypted_vault = pwd_manager.get_encrypted_vault()
			hashed_settings = settings.get_hashed_settings()

			self.json["Vault"]		= encrypted_vault
			self.json["Settings"]	= hashed_settings

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
		Assumes self.lock is acquired
	"""
	def _set_salt_and_keys(
		self,
		salt		: bytes,
		vault_key	: bytes,
		auth_key	: bytes
	):
		self.salt		= salt
		self.vault_key	= vault_key
		self.auth_key	= auth_key

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def create_settings(self) -> Settings:
		with self.lock:
			auth_key	= self.auth_key
			salt		= self.salt

		return Settings.from_key(
			key=auth_key,
			salt=salt,
			sync_callback=self.sync_settings,
			lock=self.lock,
		)

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