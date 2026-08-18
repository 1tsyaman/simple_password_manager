import os
import sys
import importlib

from pathlib import Path
from core.pwd_manager import PwdManager

from kivy.utils import platform

class VaultLoadResult:
	def __init__(self, result: PwdManager| str, error : bool = False) -> None:
		self.error = error
		self.result = result

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

def load_vault_for_gui(app_data_path: str, vault_name: str, pwd: str) -> VaultLoadResult:
	path = os.path.join(app_data_path, vault_name)

	return load_vault(path=path, pwd=pwd)

def load_vault(path: str, pwd: str) -> VaultLoadResult:
	if not Path(path).exists():
			return VaultLoadResult(result="Vault path is incorrect", error=True)

	pwd_manager = PwdManager.from_encrypted_file(path, pwd)

	if pwd_manager.error:
		return VaultLoadResult(error=True, result=pwd_manager.result)

	return VaultLoadResult(result=pwd_manager.result)

def create_and_load_vault(path: str, pwd: str) -> VaultLoadResult:
	try:
		Path(path).touch()
	except FileNotFoundError:
		return VaultLoadResult(error=True, result=INVALID_PATH_ERROR)
	
	return_result = PwdManager.pwd_manager_from_pwd(path, pwd)

	if return_result.error:
		return VaultLoadResult(error=True, result=return_result.result)

	return VaultLoadResult(result=return_result.result)

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
