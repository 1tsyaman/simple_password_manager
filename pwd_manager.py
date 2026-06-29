from __future__ import annotations
import random as rand
from getpass import getpass
from pathlib import Path


from encrypt import encrypt_data, decrypt_data, get_key_from_pwd
from entry import Entry
from keys import derrive_key

LETTERS =	[
			'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
			'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
			'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G',
			'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
			'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
		]

DIGITS =	[
			'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
		]

SPECIAL_CHARS =	[
			'!', '"', "'", '§', '$', '%', '&', '/', '(', ')', '=', '?',
			'`', '{', '[', ']', '}', '\\', '+', '-', '*', '_', ';', ':',
		]

PWD_LENGTH =	24

NO_SUCH_ENTRY_MESSAGE = "No such entry."

class PwdManager:

	"""
		PwdManager.entries are a dictionary: key=Entry, value=encrypted_pwd.
		PwdManager.file_path is a string containing the file path containing the encrypted version.
		PwdManager._key is the encryption/decryption key.
		PwdManager._salt is the salt used with the master pwd to create the encryption/decryption key.
	"""

	def __init__(self, path="", key=bytes(0), salt=bytes(0)):
		self.entries: dict[Entry, str]		= {}
		self.file_path: str			= path
		self._key: bytes			= key
		self._salt: bytes			= salt


	"""
		Does nothing if entry is already in the list (should use modify_entry instead)
	"""
	def add_entry(self: PwdManager, website: str, username: str, password: str, description: str) -> None:
		entry = Entry.create_entry(website, username, description)

		if not self.entry_exists(entry):
			return self.__add_entry_value_to_key(entry, password)

		print("An entry with the same website-username combination already exists! You can either modify it or remove it and start over.")


	"""
		If no username is provided, all entries associated with the website will be deleted
	"""
	def remove_entry(self: PwdManager, website: str, username="") -> None:
		if username == "":
			return self.remove_website_entries(website)

		entry = Entry.create_entry(website, username, "")

		reference = self._get_entry_reference_or_None(entry)

		if reference is not None:
			self.__remove_entry(reference)


	def get_password(self: PwdManager, website: str, username: str) -> str:
		entry = self.__get_entry_with_username_or_None(website, username)

		if (entry is not None):
			return self.entries[entry]

		return NO_SUCH_ENTRY_MESSAGE

	def __get_entry_with_username_or_None(self: PwdManager, website: str, username: str) -> Entry | None:
		entry = Entry.create_entry(website, username)

		for e in self.entries:
			if e.is_equal(entry):
				return e

		return None

	def _get_entry_reference_or_None(self: PwdManager, entry: Entry) -> Entry | None:
		for e in self.entries:
			if e.is_equal(entry):
				return e
		
		return None

	def entry_exists(self: PwdManager, entry: Entry) -> bool:
		if self._get_entry_reference_or_None(entry) is not None:
			return True
	
		return False
	
	
	def get_website_list(self: PwdManager) -> list[str]:
		return 	[
				entry.get_website()
							for entry in self.entries
			]
	
	
	def get_username_and_description(self: PwdManager, website: str) -> list[tuple[str, str]]:
		return 	[
				(entry.get_username(), entry.get_description())
										for entry in self.entries
			]


	def __remove_entry(self: PwdManager, entry: Entry) -> None:
		self.entries.pop(entry)

	"""
		Assumes entry does not exist in the list (simply overrides the value otherwise)
	"""
	def __add_entry_value_to_key(self: PwdManager, entry: Entry, password: str) -> None:
		self.entries[entry] = password

	def remove_website_entries(self: PwdManager, website: str) -> None:
		for entry in list(self.entries):		# similar to creating a list of keys and iterating over it rather than
								# iterating over the dictionary while modifying it
			if entry.get_website().strip().lower() == website.strip().lower():
				del self.entries[entry]

	def encrypt_and_exit(self: PwdManager) -> None:
		data = {
			f"{entry.get_website()}, {entry.get_username()}, {entry.get_description()}":	self.entries[entry]
    			
				for entry in self.entries
		}

		if self.file_path == "" or not Path(self.file_path).exists():
			return print("File path is not valid!")

		encrypt_data(data=data, key=self._key, salt=self._salt, file_path=self.file_path, associated_data="")

	"""
		decrypted_data has the following form:
		{
			"website, username, description": password,
			.
			.
			.
		}
	"""
	@staticmethod
	def from_encrypted_file(path: str) -> PwdManager | None:
		pwd_manager = PwdManager()
		pwd_manager.file_path = path

		pwd = getpass("Enter your master password:")
	
		try:
			salt, key = get_key_from_pwd(pwd, path)
			pwd_manager._key = key
			pwd_manager._salt = salt

			data: dict[str, str] = decrypt_data(key, path)
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

		try:
			for tup in data:
				website, username, description = tup.split(",", 2)
				pwd_manager.add_entry(website=website, username=username, description=description, password=data[tup])
		except:
			print("Something went wrong during descrption of vault: vault does not have the correct foramt.")
			return pwd_manager

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