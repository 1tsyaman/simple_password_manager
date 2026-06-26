from getpass import getpass
from pathlib import Path

class PwdManager:
	def __init__(self):
		self.entries	= []
		self.file_path	= None

	def sync(self):
		pass

	@staticmethod
	def from_encrypted_file(path: str):
		pwd_manager = PwdManager()
		# TODO check that the path is valid (probably should have encrypt/decrypt function do it)

		pwd_manager.file_path = Path(path)