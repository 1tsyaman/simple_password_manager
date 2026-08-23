import os

from collections.abc import Callable
from shutil import copy2

from kivymd.uix.filemanager import MDFileManager

class ImportFilePicker(MDFileManager):
	def __init__(
		self,
		app_data_path: str,
		refresh_callback: Callable,
		*args,
		**kwargs
	):
		self.app_data_path = app_data_path
		self.refresh_callback = refresh_callback

		super().__init__(
			select_path=self.import_file,
			exit_manager=lambda *args: self.close(),
			ext=[".vault"],
			search="all",
			preview=False,
			*args,
			**kwargs
		)

	def open(self):
		home_dir = os.path.expanduser("~")
		self.show(home_dir)

	def import_file(self, path: str):
		copy2(
			src=path,
			dst=self.app_data_path
		)

		self.refresh_callback()