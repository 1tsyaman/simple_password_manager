import os
import sys
import importlib
from pathlib import Path
from storage.constants import DEBUG


def get_bundled_resource(relative_path: str) -> Path:
	if getattr(sys, "frozen", False):
		base = Path(getattr(sys, "_MEIPASS"))
	else:
		base = Path.cwd()

	return base / relative_path

def get_user_data_path(relative_path: str) -> Path:
	return get_app_data_path() / relative_path

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