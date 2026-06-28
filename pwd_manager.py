from getpass import getpass
from pathlib import Path
import random as rand

from encrypt import encrypt_data_key, decrypt_data_key, get_key
from entry import Entry
from keys import derrive_key

LETTERS =	[
			'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
			'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
			'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G',
			'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
			'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
		]



DIGITS =	['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

SPECIAL_CHARS =	[
			'!', '"', "'", '§', '$', '%', '&', '/', '(', ')', '=', '?',
			'`', '{', '[', ']', '}', '\\', '+', '-', '*', '_', ';', ':',
		]

PWD_LENGTH =	24

class PwdManager:

	"""
		PwdManager.entries are a dictionary: key=website, value=Entry.
		PwdManager.file_path is a string containing the file path containing the encrypted version.
	"""

	def __init__(self, path="", key=bytes(0), salt=bytes(0)):
		self.entries: dict[str, list[Entry]]	= {}
		self.file_path: str			= path
		self._key: bytes			= key
		self._salt: bytes			= salt

	def add_entry(self: PwdManager, website: str, username: str, password: str, description: str) -> None:
		entry = Entry.create_entry(username, password, description)
		self.__add_entry_value_to_key(website, entry)

	"""
		If username is the empty string, all entries associated with the website will be deleted
	"""
	def remove_entry(self: PwdManager, website: str, username: str) -> None:
		if username == "":
			return self.remove_website_entries(website)
		
		if website in self.entries:
			entry = self.__get_entry_with_username_or_None(website, username)
			if entry:
				self.__remove_entry(website, entry)

	def get_password(self: PwdManager, website: str, username: str) -> str:
		entry = self.__get_entry_with_username_or_None(website, username)

		if (entry):
			return entry.get_password()

		return "No such entry."

	def __remove_entry(self: PwdManager, website: str, entry: Entry) -> None:
		self.entries[website].remove(entry)

	def __add_entry_value_to_key(self: PwdManager, website: str, entry: Entry) -> None:
		if website not in self.entries:
			self.entries[website] = []

		self.entries[website].append(entry)

	def __get_entry_with_username_or_None(self: PwdManager, website: str, username: str) -> Entry | None:
		for entry in self.entries[website]:
			if entry.get_username() == username:
				return entry

		return None


	def remove_website_entries(self: PwdManager, website: str) -> None:
		if website in self.entries:
			self.entries.pop(website)

	def encrypt_and_exit(self: PwdManager) -> None:
		data = {
			website:	[
				entry.get_json()
    							for entry in self.entries[website]
			]
   			for website in self.entries
		}

		if self.file_path == "" or not Path(self.file_path).exists():
			return print("File path is not valid!")

		encrypt_data_key(data=data, key=self._key, salt=self._salt, file_path=self.file_path, associated_data="")

	"""
		decrypted_data has the following form:
		{
			website:	[
						{
							"username":	value,
							"password":	value,
							"description":	value
						},
						.
						.
						.
					]
		}
	"""
	@staticmethod
	def from_encrypted_file(path: str) -> PwdManager | None:
		pwd_manager = PwdManager()
		pwd_manager.file_path = path

		pwd = getpass("Enter your master password:")
	
		try:
			salt, key = get_key(pwd, path)
			pwd_manager._key = key
			pwd_manager._salt = salt

			data: dict[str, list[dict[str, str]]] = decrypt_data_key(key, path)
		except FileNotFoundError as e:
			print(e)
			return

		except ValueError as e:
			print(e)
			return

		except KeyError as e:
			print(f"Something went wrong: {e}")
			return

		print(f"{path} decryption successful!")

		for website, entries in data.items():
			for entry in entries:
				username = entry["username"]
				password = entry["password"]
				description = entry["description"]
				pwd_manager.add_entry(website, username, password, description)

		print("Entries loaded successfully!")

		return pwd_manager
	
	@staticmethod
	def pwd_manager_from_pwd(file_path: str, pwd: str):
		salt, key = derrive_key(pwd)

		return PwdManager(file_path, key, salt)

	@staticmethod
	def generate_pwd():
		CHARS = LETTERS + DIGITS + SPECIAL_CHARS
		pwd = ""

		for i in range(PWD_LENGTH):
			pwd += rand.choice(CHARS)

		return pwd