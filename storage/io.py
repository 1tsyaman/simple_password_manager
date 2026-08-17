import os
import sys
import importlib

from pathlib import Path
from core.pwd_manager import PwdManager

from kivy.utils import platform

INVALID_PATH_ERROR	= "Given vault path does not exist"
DEBUG = True

"""
	@returns the private app data path if on android
	@returns the executable binary directory if on windows/linux

	@raises RunTimeError if run on an unsupported platform
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

def get_vault_list(dir: str) -> list[str]:
	return [file for file in os.listdir(dir) if file.endswith(".vault")]

def load_vault(path: str, pwd: str) -> PwdManager | None:
	if not Path(path).exists():
			print("Vault path is incorrect")
			return None

	return PwdManager.from_encrypted_file(path, pwd)

def create_and_load_vault(path: str, pwd: str) -> PwdManager | None:
	try:
		Path(path).touch()
	except FileNotFoundError:
		raise FileNotFoundError(INVALID_PATH_ERROR)
	
	return PwdManager.pwd_manager_from_pwd(path, pwd)

def vault_exists(path: str) -> bool:
	return Path(path).exists()

"""
	raises FileNotFound if path is incorrect
	raises OSError if path is a directory
"""
def delete_vault(path: str) -> None:
	try:
		os.remove(Path(path))
	except FileNotFoundError:
		raise FileNotFoundError(INVALID_PATH_ERROR)
	except OSError:
		raise OSError("Given vault path is a directory")
