import os
import sys
import json
import importlib
from pathlib import Path

from core.pwd_manager import PwdManager
from core.vault_loader import VaultSession
from core.errors import (
	InvalidJSONError,
)
from storage.constants import (
	VAULT_ENDING,
	DEBUG
)
"""
	@returns the private app data path if on android
	@returns the executable binary directory if on windows/linux

	@raises:
		- RuntimeError: unsupported platform
		- ModuleNotFoundError: android.storage is unavailable
		- OSError: resolving the executable/source path fails
"""
def get_app_data_path() -> Path:
	from kivy.utils import platform

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
	@returns:
		List of vault names in the dir (without the ending .vault)
	@raises:
		- OSError
"""
def get_vault_list(dir: str) -> list[str]:
	return [file[:-6] for file in os.listdir(dir) if file.endswith(VAULT_ENDING)]

"""
	@raises:
			- PasswordError
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- VaultFormatError
			- CorruptedVaultError
			- InconsistentVaultState
			- OSError
"""
def load_vault_for_gui(app_data_path: str, vault_name: str, pwd: str) -> PwdManager:
	path = os.path.join(app_data_path, vault_name + VAULT_ENDING)

	return load_vault(path=path, pwd=pwd)

"""
	@raises:
			- PasswordError
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- VaultFormatError
			- CorruptedVaultError
			- InconsistentVaultState
			- OSError
"""
def load_vault(path: str, pwd: str) -> PwdManager:
	dir				= os.path.dirname(path)
	vault_name, _	= os.path.splitext(os.path.basename(path))
	vault_session = VaultSession(
		app_data_path=dir,
		vault_name=vault_name,
		password=pwd
	)

	return vault_session.get_pwd_manager()

"""
	@raises:
		- FileNotFoundError
		- OSError
		- InvalidJSONError

"""
def load_settings(path: str) -> dict[str, dict]:
	try:
		with open(path, 'r', encoding="utf-8") as fd:
			return json.load(fd)
	except (json.JSONDecodeError, UnicodeDecodeError):
		raise InvalidJSONError

"""
	@raises:
		- FileNotFoundError(path) [OSError]
		- PasswordRequirementsError(reason)
		- KeyLengthError
		- KeyDerivationError
		- OSError
"""
def create_and_load_vault(path: str, pwd: str) -> PwdManager:
	dir				= os.path.dirname(path)
	vault_name, _	= os.path.splitext(os.path.basename(path))
	vault_session = VaultSession(
		app_data_path=dir,
		vault_name=vault_name,
		password=pwd,
		new_vault=True
	)

	return vault_session.create_pwd_manager()

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
	path = os.path.join(app_data_path, vault_name + VAULT_ENDING)
	return Path(path).exists()

"""
	@raises: 
		- OSError
"""
def delete_file(path: str) -> None:
	os.remove(Path(path))

"""
	@raises: 
		- OSError
"""
def delete_vault_for_gui(
	app_data_path: str,
	vault_name: str
):
	path = os.path.join(app_data_path, vault_name + VAULT_ENDING)
	delete_file(path)

def rename_vault(
		path: str,
		vault_name: str,
		new_vault_name: str
):
	old_path = os.path.join(path, vault_name + VAULT_ENDING)
	new_path = os.path.join(path, new_vault_name + VAULT_ENDING)

	os.rename(old_path, new_path)


def get_unique_image_path_with_prefix(
	dir: str,
	image_prefix: str
) -> str:
	for file in os.listdir(dir):
		if file.startswith(image_prefix):
			return os.path.join(dir, file)

	raise FileNotFoundError

"""
	Assumes that path is a path/to/file
"""
def create_path(path: str):
	directory_path = os.path.dirname(path)

	if directory_path != "":
		os.makedirs(directory_path, exist_ok=True)

	# create the file
	open(path, 'a').close()