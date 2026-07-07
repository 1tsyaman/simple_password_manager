import os

from pathlib import Path
from core.pwd_manager import PwdManager

INVALID_PATH_ERROR	= "Given vault path does not exist"

def load_vault(path: str) -> PwdManager | None:
	if not Path(path).exists():
			print("Vault path is incorrect")
			return None

	return PwdManager.from_encrypted_file(path)

def create_and_load_vault(path: str) -> PwdManager | None:
	try:
		Path(path).touch()
	except FileNotFoundError:
		raise FileNotFoundError(INVALID_PATH_ERROR)
	
	return PwdManager.pwd_manager_from_pwd(path)

def vault_exists(path: str) -> bool:
	return Path(path).exists()

"""
	raises FileNotFound if path is incorrect
	raises OSError if path is a directory
"""
def delete_vault(path: str) -> None:
	try:
		os.remove(Path(path))
	except FileExistsError:
		raise FileExistsError(INVALID_PATH_ERROR)
	except OSError:
		raise OSError("Given vault path is a directory")
