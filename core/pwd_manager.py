from __future__ import annotations
import random as rand
from pathlib import Path
from pyotp import TOTP
from hashlib import sha1
from time import sleep

from core.encrypt import encrypt_data, decrypt_data, get_key_from_pwd
from core.entry import Entry
from core.keys import derrive_key
from core.totp import TOTP_Config

LETTERS_LOWER =	[
			'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
			'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
			'w', 'x', 'y', 'z'
		]

LETTERS_UPPER = [
			'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
			'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
			'W', 'X', 'Y', 'Z'
		]

DIGITS =	[
			'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
		]

SPECIAL_CHARS =	[
			'!', '"', '#', '$', '%', '&', "'", '(', ')', '*',
			'+', ',', '-', '.', '/', ':', ';', '<', '=', '>',
			'?', '@', '[', '\\', ']', '^', '_', '`', '{', '|',
			'}', '~'
		]

PWD		= "pwd"
TOTP_SECRET	= "totp_secret"
TOTP_URI	= "totp_uri"

#	For websites that are picky about special characters
"""
SPECIAL_CHARS = [char for char in r"#()+,-_./"]
"""

MIN_PWD_LENGTH	=	8
PWD_LENGTH	=	24

NO_SUCH_ENTRY_MESSAGE	= "No such entry."
NO_SUCH_TOTP_MESSAGE	= "There is no TOTP config associated with this entry"
URI_INVALID_MESSAGE	= "Provided TOTP URI is invalid."

class PwdManager:

	"""
		PwdManager.entries are a dictionary: key=Entry, value={
									PWD: 		pwd,
									TOTP_SECRET: 	secret,
									TOTP_URI:	uri
								}
		PwdManager.file_path is a string containing the file path containing the encrypted version.
		PwdManager._key is the encryption/decryption key.
		PwdManager._salt is the salt used with the master pwd to create the encryption/decryption key.
		PwdManager._totp is the TOTP object associated with this account
	"""
	def __init__(self, path="", key=bytes(0), salt=bytes(0)):
		self.entries: dict[Entry, dict[str, str]]		= {}
		self.file_path: str					= path
		self._key: bytes					= key
		self._salt: bytes					= salt

	"""
		Does nothing if entry is already in the list (should use modify_entry instead)
		Does not set totp config (should be done in a separate stage)
	"""
	def add_entry(self: PwdManager, website: str, username: str, password: str, description: str) -> None:
		entry = Entry.create_entry(website, username, description)

		if not self.entry_exists(entry):
			return self.__add_entry_pwd_to_key(entry, password)

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

	def modify_master_password(self: PwdManager, pwd: str) -> None:
		salt, key = derrive_key(pwd)
		self._key = key
		self._salt = salt

		# rewrite the vault file to update the password
		self.encrypt()

	def get_password(self: PwdManager, website: str, username: str) -> str:
		entry = self.__get_entry_with_username_or_None(website, username)

		if (entry is not None):
			return self.entries[entry][PWD]

		return NO_SUCH_ENTRY_MESSAGE
	
	def get_totp(self: PwdManager, website: str, username: str) -> str:
		entry = self.__get_entry_with_username_or_None(website, username)

		if entry is None:
			return NO_SUCH_ENTRY_MESSAGE

		totp_config = entry.get_totp_config()

		if totp_config is None:
			return NO_SUCH_TOTP_MESSAGE
				
		secret = self.entries[entry][TOTP_SECRET]

		return f"Code: {TOTP(s=secret, digits=totp_config.digits, digest=sha1, interval=totp_config.period).now()}. Valid for {totp_config.seconds_remaining()} seconds."

	def has_totp(self: PwdManager, website: str, username: str) -> bool:
		entry = self.__get_entry_with_username_or_None(website, username)

		if entry is None:
			return False

		return entry.get_totp_config() is not None

	def set_password(self: PwdManager, website: str, username: str, password: str):
		entry = self.__get_entry_with_username_or_None(website, username)

		if entry is None:
			return NO_SUCH_ENTRY_MESSAGE
		
		self.entries[entry][PWD] = password
	
	def set_totp_config(self: PwdManager,website: str, username: str, uri: str):
		entry = self.__get_entry_with_username_or_None(website=website, username=username)

		if entry is None:
			return NO_SUCH_ENTRY_MESSAGE
	
		config = TOTP_Config.from_uri(uri)
		
		if config is None:
			return URI_INVALID_MESSAGE
		
		totp_config, secret = config

		entry.set_totp_config(totp_config=totp_config)
		self.entries[entry][TOTP_SECRET] = secret
		self.entries[entry][TOTP_URI] = uri

			
	def get_entry_list(self: PwdManager) -> list[Entry]:
		return [entry for entry in self.entries]

	def get_entry_by_index(self: PwdManager, index: int) -> Entry:
		ls = list(self.entries)
		
		if index < 0 or index > len(self.entries) - 1:
			raise IndexError("Trying to access an entry with an invalid index!")

		entry = ls[index]

		return entry

	def entry_exists(self: PwdManager, entry: Entry) -> bool:
		if self._get_entry_reference_or_None(entry) is not None:
			return True
	
		return False

	def get_username_and_description(self: PwdManager, website: str) -> list[tuple[str, str]]:
		return 	[
				(entry.get_username(), entry.get_description())
										for entry in self.entries if entry.get_website() == website
		]

	def get_website_and_username_string(self: PwdManager) -> list[str]:
		return [entry.to_string() for entry in self.entries]

	def get_entry_list_len(self: PwdManager) -> int:
		return len(self.entries)

	def get_entries_by_website(self: PwdManager, website: str) -> list[Entry]:
		return [
			entry for entry in self.entries if entry.get_website() == website
		]

	def get_entries_by_username(self: PwdManager, username: str) -> list[Entry]:
		return [
			entry for entry in self.entries if entry.get_username() == username
		]

	def remove_website_entries(self: PwdManager, website: str) -> None:
		for entry in list(self.entries):		# similar to creating a list of keys and iterating over it rather than
								# iterating over the dictionary while modifying it
			if entry.get_website().strip().lower() == website.strip().lower():
				del self.entries[entry]

	"""
		encrypts the PwdManager object and writes it into the vault file
		{
			"(website, username, description)": {
								PWD: 		password,
								TOTP_URI	uri
							}
		}
	"""
	def encrypt(self: PwdManager) -> None:
		data = {
			f"{entry.get_website()}, {entry.get_username()}, {entry.get_description()}":
				{
					PWD: self.entries[entry][PWD],
					TOTP_URI: self.entries[entry][TOTP_URI]
				}
				for entry in self.entries
		}

		if self.file_path == "" or not Path(self.file_path).exists():
			return print("File path is not valid!")

		encrypt_data(data=data, key=self._key, salt=self._salt, file_path=self.file_path, associated_data="")


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


	def __remove_entry(self: PwdManager, entry: Entry) -> None:
		self.entries.pop(entry)

	"""
		Assumes entry does not exist in the list (simply overrides the value otherwise)
	"""
	def __add_entry_pwd_to_key(self: PwdManager, entry: Entry, password: str) -> None:
		self.entries[entry] = {
			PWD: password,
			TOTP_SECRET: "",
			TOTP_URI: ""
		}

	"""
		decrypted_data has the following form:
		{
			"website, username, description": {
								PWD: 		"password",
								TOTP_URI: 	"valid_uri" 
							  },
			.
			.
			.
		}
	"""
	@staticmethod
	def from_encrypted_file(path: str, pwd: str) -> PwdManager | None:
		satisfies, reason = PwdManager._pwd_satisfies_conditions(pwd, len_min=MIN_PWD_LENGTH)

		if not satisfies:
			raise KeyError(f"Password does not meet the minimum requirements: {reason}")

		pwd_manager = PwdManager()
		pwd_manager.file_path = path


		try:
			salt, key = get_key_from_pwd(pwd, path)
			pwd_manager._key = key
			pwd_manager._salt = salt

			data = decrypt_data(key, path)
		except FileNotFoundError as e:
			print(e)
			return

		except ValueError as e:
			print(e)
			return

		except KeyError as e:
			print(f"Something went wrong: {e}")
			return

		if not PwdManager._has_new_format(data):

			if PwdManager._has_old_format(data):
				print("Vault is in old format. Please save before quitting to convert it to the new format.")
				sleep(1)
				return PwdManager._from_encrypted_file_old(path, pwd)
			
			print("Something went wrong during descrption of vault: vault does not have the correct foramt.")
			return None

		print(f"{path} decryption successful!")

		for tup in data:
			website, username, description = (
				value.strip()
				for value in tup.split(",", 2)
			)
			pwd_manager.add_entry(website=website, username=username, description=description, password=data[tup][PWD])
			
			uri = data[tup][TOTP_URI]

			if len(uri) > 0:
				message = pwd_manager.set_totp_config(website=website, username=username, uri=uri)

				if message == URI_INVALID_MESSAGE:
					# data loss warning message (should not happen normally)
					print(f"Invalid TOTP URI for entry ({website}, {username}).")
					sleep(5)
			
		print("Entries loaded successfully!")

		return pwd_manager
	
	"""
		*This is the old format (pre TOTP support)*

		decrypted_data has the following form:
		{
			"website, username, description": password,
			.
			.
			.
		}
	"""
	@staticmethod
	def _from_encrypted_file_old(path: str, pwd: str) -> PwdManager | None:
		satisfies, reason = PwdManager._pwd_satisfies_conditions(pwd, len_min=MIN_PWD_LENGTH)

		if not satisfies:
			raise KeyError(f"Password does not meet the minimum requirements: {reason}")

		pwd_manager = PwdManager()
		pwd_manager.file_path = path


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
				website, username, description = (
					value.strip()
					for value in tup.split(",", 2)
				)
				pwd_manager.add_entry(website=website, username=username, description=description, password=data[tup])
		except:
			print("Something went wrong during descrption of vault: vault does not have the correct foramt.")
			return pwd_manager

		print("Entries loaded successfully!")

		return pwd_manager

	@staticmethod
	def  pwd_manager_from_pwd(file_path: str, pwd: str) -> PwdManager:
		satisfies, reason = PwdManager._pwd_satisfies_conditions(pwd, len_min=MIN_PWD_LENGTH)

		if not satisfies:
			raise KeyError(f"Password does not meet the minimum requirements: {reason}")

		return PwdManager._pwd_manager_from_pwd(file_path, pwd)

	"""
		creates a PwdManager object and initializes the vault file
	"""
	@staticmethod
	def _pwd_manager_from_pwd(file_path: str, pwd: str) -> PwdManager:
		salt, key = derrive_key(pwd)
		
		pwd_manager = PwdManager(file_path, key, salt)

		pwd_manager.encrypt()

		return pwd_manager

	@staticmethod
	def generate_pwd():
		CHARS = LETTERS_LOWER + LETTERS_UPPER + DIGITS + SPECIAL_CHARS
		while True:
			pwd = ""

			for i in range(PWD_LENGTH):
				pwd += rand.choice(CHARS)
			
			satisfies, _ = PwdManager._pwd_satisfies_conditions(pwd)
			if satisfies:
				break

		return pwd
	
	@staticmethod
	def _pwd_satisfies_conditions(pwd: str, len_min=PWD_LENGTH) -> tuple[bool, str]:
		if len(pwd) < len_min:
			return False, 'len'

		for digit in DIGITS:
			if digit in pwd:
				break
		else:
			return False, 'digit'

		for letter in LETTERS_LOWER:
			if letter in pwd:
				break
		else:
			return False, 'lower'
		
		for letter in LETTERS_UPPER:
			if letter in pwd:
				break
		else:
			return False, 'upper'
		
		for spec in SPECIAL_CHARS:
			if spec in pwd:
				break
		else:
			return False, 'special'

		return True, ''
	
	@staticmethod
	def _has_new_format(data: dict) -> bool:
		return all(
			isinstance(data, dict)
			and isinstance(key, str)
			and len(key.split(",", 2)) == 3
			and isinstance(value, dict)
			and isinstance(value.get(PWD), str)
			and isinstance(value.get(TOTP_URI), str)
				for key, value in data.items()
		)
	
	@staticmethod
	def _has_old_format(data: object) -> bool:
		return isinstance(data, dict) and all(
			isinstance(key, str)
			and len(key.split(",", 2)) == 3
			and isinstance(value, str)
			for key, value in data.items()
		)