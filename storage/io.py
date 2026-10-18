import os
import json
from pathlib import Path

from core.etc.errors import (
	InvalidJSONError,
)
from storage.constants import (
	VAULT_ENDING,
)


"""
	@returns:
		List of vault names in the dir (without the ending .vault)
	@raises:
		- OSError
"""
def get_vault_list(dir: str) -> list[str]:
	return [file[:-6] for file in os.listdir(dir) if file.endswith(VAULT_ENDING)]


def get_dir_path_and_vault_name(path: str) -> tuple[str, str]:
	dir				= os.path.dirname(path)
	vault_name, _	= os.path.splitext(os.path.basename(path))

	return dir, vault_name

"""
	@raises:
		- FileNotFoundError
		- OSError
		- InvalidJSONError
"""
def load_json(path: str) -> dict[str, dict]:
	try:
		with open(path, 'r', encoding="utf-8") as fd:
			return json.load(fd)
	except (json.JSONDecodeError, UnicodeDecodeError):
		raise InvalidJSONError


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

def delete_folder(path: str) -> None:
	os.rmdir(path)

def move_file(
	src: str,
	dst: str
) -> None:
	"""
		Raises:
			OSError
	"""
	os.replace(src, dst)

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