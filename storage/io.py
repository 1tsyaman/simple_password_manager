import os
import sys
import importlib
from kivy.utils import platform
from pathlib import Path

from core.pwd_manager import PwdManager

INVALID_PATH_ERROR	= "Given vault path does not exist"
DEBUG = True

"""
	@returns the private app data path if on android
	@returns the executable binary directory if on windows/linux

	@raises:
		- RuntimeError: unsupported platform
		- ModuleNotFoundError: android.storage is unavailable
		- OSError: resolving the executable/source path fails
"""
def get_app_data_path() -> Path:
	# TODO: remove before bundling app
	if DEBUG:
		return Path('C://Users//y-fao//Desktop//Aktuell//Others//password_manager//')

	if platform == "android":
		android_storage = importlib.import_module("android.storage")
		return Path(android_storage.app_storage_path())

	if os.name in ("nt", "posix"):
		if getattr(sys, "frozen", False):
			return Path(sys.executable).resolve().parent

		return Path(__file__).resolve().parent

	raise RuntimeError(f"Unsupported platform: {platform}")

"""
	@raises:
		- OSError
"""
def get_vault_list(dir: str) -> list[str]:
	return [file for file in os.listdir(dir) if file.endswith(".vault")]

"""
	@raises:
			- PasswordError
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- VaultFormatError
			- CorruptedVaultError
			- OSError
"""
def load_vault_for_gui(app_data_path: str, vault_name: str, pwd: str) -> PwdManager:
	path = os.path.join(app_data_path, vault_name)

	return load_vault(path=path, pwd=pwd)

"""
	@raises:
			- PasswordError
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- VaultFormatError
			- CorruptedVaultError
			- OSError
"""
def load_vault(path: str, pwd: str) -> PwdManager:
	if not Path(path).exists():
		raise FileNotFoundError

	pwd_manager = PwdManager.from_encrypted_file(path, pwd)

	return pwd_manager

"""
	@raises:
		- FileNotFoundError(path) [OSError]
		- PasswordRequirementsError(reason)
		- KeyLengthError
		- KeyDerivationError
		- OSError
"""
def create_and_load_vault_for_gui(app_data_path: str, vault_name: str, pwd: str) -> PwdManager:
	path = os.path.join(app_data_path, vault_name + ".vault")

	try:
		return create_and_load_vault(path=path, pwd=pwd)
	except Exception:
		os.remove(path)	# remove file if created
		raise			# raise the exception that was caught here

"""
	@raises:
		- FileNotFoundError(path) [OSError]
		- PasswordRequirementsError(reason)
		- KeyLengthError
		- KeyDerivationError
		- OSError
"""
def create_and_load_vault(path: str, pwd: str) -> PwdManager:
	
	Path(path).touch()
	
	pwd_manager = PwdManager.pwd_manager_from_pwd(path, pwd)

	return pwd_manager

"""
	@raises:
		- OSError
"""
def vault_exists(path: str) -> bool:
	return Path(path).exists()

"""
	@raises:
		- OSError
"""
def vault_exists_for_gui(app_data_path: str, vault_name: str):
	path = os.path.join(app_data_path, vault_name + ".vault")
	return Path(path).exists()

"""
	@raises: 
		- OSError
"""
def delete_vault(path: str) -> None:
	os.remove(Path(path))
