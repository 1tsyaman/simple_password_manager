import os

from storage.constants import VAULT_ENDING
from core.encrypt import get_salt_from_vault
from core.keys import derive_master_key, derive_subkey, get_random_salt
from core.pwd_manager import PwdManager
from core.settings import Settings
from core.passwords import password_satisfies_explicit_conditions
from core.errors import (
	PasswordError,
	PasswordRequirementsError
)

import storage.io as io

class VaultSession:
	vault_path	: str
	vault_key	: bytes
	auth_key	: bytes
	salt		: bytes

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

		self.app_data_path	= app_data_path
		self.vault_path		= os.path.join(app_data_path, vault_name + VAULT_ENDING)

		if new_vault:
			self.salt = get_random_salt()
			io.create_path(self.vault_path)
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
		settings	: Settings | None = None	# temporary
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

		if settings is not None:
			settings.set_key_salt_pair(
				key=self.auth_key,
				salt=self.salt
			)

		"""
			TODO: Encrypt both atomically -> one json file
			{
				"vault":	{actual vault json content},
				"settings":	{actual settings json content}
			}
		"""

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
		return PwdManager.from_encrypted_file_key(
			path=self.vault_path,
			key=self.vault_key,
			salt=self.salt
		)

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- OSError
	"""
	def create_pwd_manager(self) -> PwdManager:
		return PwdManager.pwd_manager_from_key(
			path=self.vault_path,
			key=self.vault_key,
			salt=self.salt
		)

	"""
		@raises:
			- NoSettingsFileError
			- InvalidSettingsFile
			- SettingsFileModifiedError
			- OSError
	"""
	def get_settings(self) -> Settings:
		return Settings.load_settings(
			app_data_path=self.app_data_path,
			key=self.auth_key,
			salt=self.salt
		)

	"""
		@raises:
			- SettingsKeyNotSetError
			- OSError
	"""
	def create_settings(self) -> Settings:
		return Settings.from_key(
			app_data_path=self.app_data_path,
			key=self.auth_key,
			salt=self.salt
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