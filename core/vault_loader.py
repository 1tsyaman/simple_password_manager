import os

from storage.io import VAULT_ENDING
from core.encrypt import get_salt_from_vault
from core.keys import derive_master_key, derive_subkey, get_random_salt
from core.pwd_manager import PwdManager
from core.settings import Settings

class VaultSession:
	vault_path	: str
	vault_key	: bytes
	auth_key	: bytes
	salt		: bytes

	"""
		@raises:
			- FileNotFoundError(path) [OSError]
			- VaultFormatError
			- OSError
	"""
	def __init__(
		self,
		app_data_path	: str,
		vault_name		: str,
		password		: str,
		new_vault		: bool = False
	) -> None:
		self.app_data_path	= app_data_path
		self.vault_path		= os.path.join(app_data_path, vault_name + VAULT_ENDING)

		if new_vault:
			self.salt = get_random_salt()
		else:
			self.salt = get_salt_from_vault(self.vault_path)

		# derrive master key
		_, master_key = derive_master_key(
			pwd=password,
			salt=self.salt
		)

		self.vault_key = derive_subkey(
			master_key=master_key,
			purpose="vault-encryption"
		)
		self.auth_key = derive_subkey(
			master_key=master_key,
			purpose="settings-auth"
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