from __future__ import annotations
import random as rand
from pyotp import TOTP
from hashlib import sha1
from time import sleep
from copy import deepcopy

from core.encrypt import (
	encrypt_data,
	decrypt_data,
	get_key_from_pwd
)
from core.entry import Entry
from core.keys import derive_key
from core.totp import TOTP_Config
from core.errors import (
	PasswordError,
	PasswordRequirementsError,
	EntryExistsError,
	NoSuchEntryError,
	TotpUriError,
	TotpQRCodeError,
	InconsistentVaultState,
	VaultFormatError,
	ImageOpenError,
	QRDecodeError,
	log
)

from storage.qr_reader import read_qr_code

# Config
LETTERS_LOWER	= [l for l in "abcdefghijklmnopqrstuvwxyz"]
LETTERS_UPPER	= [l.upper() for l in LETTERS_LOWER]
DIGITS			= [d for d in "1234567890"]
SPECIAL_CHARS	= [s for s in "!\"#$%&'()*+,-./:<=>?@[\\]^_`{|}~"]
MIN_PWD_LENGTH	= 8
PWD_LENGTH		= 24

# Keywords
PWD			= "pwd"
TOTP_SECRET	= "totp_secret"
TOTP_URI	= "totp_uri"


URI_INVALID_MESSAGE	= "Provided TOTP URI is invalid."

class PwdManager:
	"""
		PwdManager.entries are a dictionary: 
			key = Entry, value=	{
									PWD:			pwd,
									TOTP_SECRET:	secret,
									TOTP_URI:		uri
								}
		PwdManager.file_path is a string containing the file path containing the encrypted version.
		PwdManager._key is the encryption/decryption key.
		PwdManager._salt is the salt used with the master pwd to create the encryption/decryption key.
		PwdManager._totp is the TOTP object associated with this account
	"""
	def __init__(
		self,
		path: str	= "",
		key	: bytes = bytes(0),
		salt: bytes = bytes(0)
	):
		self.entries	: dict[Entry, dict[str, str]]	= {}
		self.file_path	: str							= path
		self._key		: bytes							= key
		self._salt		: bytes							= salt

####	Vault modifiers		####

	"""
		@raises:
			- PasswordRequirementsError(reason)
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- OverflowError
			- OSError
	"""
	def modify_master_password(
		self: PwdManager,
		pwd	: str
	) -> None:
		satisfies, reason = PwdManager._pwd_satisfies_conditions(
			pwd,
			len_min=MIN_PWD_LENGTH
		)

		if not satisfies:
			raise PasswordRequirementsError(reason=reason)

		salt, key = derive_key(pwd)
		old_key, old_salt = self._key, self._salt

		self._key	= key
		self._salt	= salt

		# rewrite the vault file to update the password
		try:
			self.encrypt()
		except BaseException:
			self._key	= old_key
			self._salt	= old_salt
			raise

	"""
		encrypts the PwdManager object and writes it into the vault file
		{
			"(website, username, description)": {
													PWD: 		password,
													TOTP_URI	uri
												}
		}

		@raises:
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- OverflowError
			- OSError
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

		encrypt_data(
			data=data,
			key=self._key,
			salt=self._salt,
			file_path=self.file_path,
			associated_data=""
		)

	"""
		Returns a carbon copy of the current password manager
	"""
	def get_snapshot(self) -> PwdManager:
		pwd_manager_copy = PwdManager(
			path=self.file_path,
			key=self._key,
			salt=self._salt
		)

		pwd_manager_copy.entries = deepcopy(self.entries)

		return pwd_manager_copy

####	Entry modifiers		####

	"""
		Does not set totp config (should be done in a separate stage)

		@raises
			- EntryExistsError
	"""
	def add_entry(
		self		: PwdManager,
		website		: str,
		username	: str,
		password	: str,
		description	: str
	) -> None:
		entry = Entry.create_entry(
			website=website,
			username=username,
			description=description
		)

		if not self.entry_exists(entry):
			return self.__add_pwd_to_entry(
				entry=entry,
				password=password
			)

		raise EntryExistsError

	"""
		@raises:
			- NoSuchEntryError
	"""
	def update_entry(
		self			: PwdManager,
		website			: str,
		username		: str,
		new_website		: str,
		new_username	: str,
		new_password	: str,
		new_description	: str		
	):
		entry = self.__get_entry_with_username_or_None(website, username)

		if entry is None:
			raise NoSuchEntryError

		entry.set_website(new_website)
		entry.set_username(new_username)
		entry.set_description(new_description)

		self.entries[entry][PWD] = new_password

	def remove_entry(
		self	: PwdManager,
		website	: str,
		username: str
	) -> None:
		entry = Entry.create_entry(
			website=website,
			username=username
		)

		reference = self._get_entry_reference_or_None(entry)

		if reference is not None:
			self.__remove_entry(reference)

####	Entry getters	####

	"""
		@raises:
			- IndexError
	"""
	def get_entry_by_index(
			self	: PwdManager,
			index	: int
	) -> Entry:
		return list(self.entries)[index]	# short-hand for list(self.entries.keys())

	def get_entry_list(self: PwdManager) -> list[Entry]:
		return [entry for entry in self.entries]

	def get_entries_by_website(
		self	: PwdManager,
		website	: str
	) -> list[Entry]:
		return [entry for entry in self.entries
					if entry.get_website() == website]

	def get_entries_by_username(
		self	: PwdManager,
		username: str
	) -> list[Entry]:
		return [entry for entry in self.entries
		  			if entry.get_username() == username]

	def get_entry_list_len(self: PwdManager) -> int:
		return len(self.entries)

	"""
		Returns a list of dictionaries
			{
				"website":		'website',
				"username":		'username',
				"description":	'description',
				"totp_config":	{
									"issuer":		'issuer',
									"account":		'account',
									"algorithm":	'algorithm',
									"digits":		digits,
									"period":		period"
								}
			}
		
		"totp_config" can be {} if there is no config set up
	"""
	def get_entries_as_json(self: PwdManager) -> list[dict]:
		return [entry.get_json()
					for entry in self.entries]

	def get_entry_as_json(
		self,
		website: str,
		username: str
	) -> dict:
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is None:
			raise NoSuchEntryError

		return entry.get_json()


####	Entry attribute getters		####

	"""
		@raises:
			- NoSuchEntryError
	"""
	def get_password(
		self	: PwdManager,
		website	: str,
		username: str
	) -> str:
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is not None:
			return self.entries[entry][PWD]

		raise NoSuchEntryError

	"""
		@raises:
			- NoSuchEntryError
			- EntryHasNoTotp
	"""
	def get_totp(
		self	: PwdManager,
		website	: str,
		username: str
	) -> tuple[str, int]:
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is None:
			raise NoSuchEntryError

		totp_config = entry.get_totp_config()

		secret = self.entries[entry][TOTP_SECRET]

		totp_code = TOTP(
			s=secret,
			digits=totp_config.digits,
			digest=sha1,
			interval=totp_config.period
		).now()
		time_remaining = totp_config.seconds_remaining()

		return totp_code, time_remaining

	def get_website_and_username_string_list(self: PwdManager) -> list[str]:
		return [entry.get_website_username_pair_string() for entry in self.entries]

	def get_website_username_pair_list(self: PwdManager) -> list[tuple[str, str]]:
		return [(entry.get_website(), entry.get_username()) for entry in self.get_entry_list()]

	"""
		@raises:
			- NoSuchEntryError
	"""
	def get_password_and_description(
		self: PwdManager,
		website: str,
		username: str
	) -> dict[str, str]:
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is None:
			raise NoSuchEntryError

		return {
			"password": 	self.get_password(
									website=website,
								  	username=username
							),
			"description":	entry.get_description()
		}

####	Entry attribute setters		####

	"""
		@raises:
			- NoSuchEntryError
	"""
	def set_password(
		self	: PwdManager,
		website	: str,
		username: str,
		password: str
	):
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is None:
			raise NoSuchEntryError

		self.entries[entry][PWD] = password


	"""
		@raises:
			- NoSuchEntryError
			- TotpQRCodeError
			- TotpUriError
	"""
	def set_totp_config_qr_code(
		self	: PwdManager,
		website	: str,
		username: str,
		qr_path	: str,
	):
		uri = self.get_uri_from_qr_code(qr_path)

		return self.set_totp_config_uri(
			website=website,
			username=username,
			uri=uri
		)

	"""
		@raises:
			- NoSuchEntryError
			- TotpUriError
	"""
	def set_totp_config_uri(
		self	: PwdManager,
		website	: str,
		username: str,
		uri		: str
	):
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is None:
			raise NoSuchEntryError

		config = TOTP_Config.from_uri(uri)

		totp_config, secret = config

		entry.set_totp_config(
			totp_config=totp_config
		)

		self.entries[entry][TOTP_SECRET]	= secret
		self.entries[entry][TOTP_URI]		= uri

####	Boolean methods		####

	def has_totp(
		self: PwdManager,
		website: str,
		username: str
	) -> bool:
		entry = self.__get_entry_with_username_or_None(
			website=website,
			username=username
		)

		if entry is None:
			return False

		return entry.has_totp()

	def entry_exists(
		self: PwdManager,
		entry: Entry
	) -> bool:
		return self._get_entry_reference_or_None(entry) is not None

####	Private methods		####

	def __remove_entry(self: PwdManager, entry: Entry) -> None:
		self.entries.pop(entry)

	def __get_entry_with_username_or_None(
		self	: PwdManager,
		website	: str,
		username: str
	) -> Entry | None:
		entry = Entry.create_entry(
			website=website,
			username=username
		)

		for e in self.entries:
			if e.is_equal(entry):
				return e

		return None

	def _get_entry_reference_or_None(
		self	: PwdManager,
		entry	: Entry
	) -> Entry | None:
		for e in self.entries:
			if e.is_equal(entry):
				return e

		return None

	"""
		Assumes entry does not exist in the list (simply overrides the value otherwise)
	"""
	def __add_pwd_to_entry(
		self: PwdManager,
		entry: Entry,
		password: str
	) -> None:
		self.entries[entry] = {
			PWD: 			password,
			TOTP_SECRET: 	"",
			TOTP_URI:		""
		}

####	Statics		####

	"""
		@raises:
			- TotpQRCodeError
	"""
	@staticmethod
	def get_uri_from_qr_code(image_path: str) -> str:
		try:
			return read_qr_code(image_path)
		except (ImageOpenError, QRDecodeError):
			raise TotpQRCodeError

	"""
		@raises:
			- TotpQRCodeError
			- TotpUriError
	"""
	@staticmethod
	def get_totp_uri_and_preview_from_qr_code(image_path: str) -> tuple[str, str]:
		uri = PwdManager.get_uri_from_qr_code(image_path)
		preview = PwdManager.get_totp_preview_from_uri(uri)

		return uri, preview

	"""
		@raises:
			- TotpUriError
	"""
	@staticmethod
	def get_totp_preview_from_uri(uri: str) -> str:
		config = TOTP_Config.from_uri(uri)

		totp_config, secret = config

		totp_code = TOTP(
			s=secret,
			digits=totp_config.digits,
			digest=sha1,
			interval=totp_config.period
		).now()

		return totp_code

	@staticmethod
	def generate_random_pwd():
		CHARS = LETTERS_LOWER + LETTERS_UPPER + DIGITS + SPECIAL_CHARS
		while True:
			pwd = ""

			for _ in range(PWD_LENGTH):
				pwd += rand.choice(CHARS)

			satisfies, _ = PwdManager._pwd_satisfies_conditions(pwd)
			if satisfies:
				break

		return pwd

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

		@raises:
			- PasswordError
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- VaultFormatError
			- CorruptedVaultError
			- InconsistentVaultState
			- OSError
	"""
	@staticmethod
	def from_encrypted_file(
		path: str,
		pwd: str
	) -> PwdManager:
		satisfies, _ = PwdManager._pwd_satisfies_conditions(
			pwd=pwd,
			len_min=MIN_PWD_LENGTH
		)

		if not satisfies:
			raise PasswordError

		pwd_manager = PwdManager()
		pwd_manager.file_path = path

		salt, key = get_key_from_pwd(
			pwd=pwd,
			file_path=path
		)

		pwd_manager._key	= key
		pwd_manager._salt	= salt

		data = decrypt_data(
			key=key,
			file_path=path
		)

		if not PwdManager._has_new_format(data):
			# Fallback
			if PwdManager._has_old_format(data):
				return PwdManager._from_encrypted_file_old(
					path=path,
					pwd=pwd
				)

			raise VaultFormatError

		for tup in data:
			website, username, description = (
				value.strip()
					for value in tup.split(",", 2)
			)

			try:
				pwd_manager.add_entry(
					website=website,
					username=username,
					description=description,
					password=data[tup][PWD]
				)

			except EntryExistsError:
				# Fallback to avoid data loss
				while True:
					random = rand.randint(1, 1000)
					website = website + f"_dup_{random}"
					try:
						pwd_manager.add_entry(
							website=website,
							username=username,
							description=description,
							password=data[tup][PWD]
						)
						break
					except EntryExistsError:
						continue

			uri = data[tup][TOTP_URI]

			if len(uri) > 0:
				try:
					pwd_manager.set_totp_config_uri(
						website=website,
						username=username,
						uri=uri
					)
				except (NoSuchEntryError, TotpUriError):
					log(
						message=f"Failed while setting up TOTP config"
					)
					raise InconsistentVaultState

		return pwd_manager

	"""
		@raises:
			- PasswordRequirementsError(reason)
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- OSError
	"""
	@staticmethod
	def pwd_manager_from_pwd(
		path	: str,
		pwd		: str
	) -> PwdManager:
		satisfies, reason = PwdManager._pwd_satisfies_conditions(
			pwd=pwd,
			len_min=MIN_PWD_LENGTH
		)

		if not satisfies:
			raise PasswordRequirementsError(
				reason=reason
			)

		pwd_manager = PwdManager._pwd_manager_from_pwd(
			path=path,
			pwd=pwd
		)
		return pwd_manager

####	Private statics		####

	"""
		*This is the old format (pre TOTP support)*

		decrypted_data has the following form:
		{
			"website, username, description": password,
			.
			.
			.
		}

		@raises:
			- PasswordError
			- FileNotFoundError [OSError]
			- KeyLengthError
			- KeyDerivationError
			- VaultFormatError
			- CorruptedVaultError
			- OSError
	"""
	@staticmethod
	def _from_encrypted_file_old(
		path	: str,
		pwd		: str
	) -> PwdManager:
		satisfies, reason = PwdManager._pwd_satisfies_conditions(
			pwd=pwd,
			len_min=MIN_PWD_LENGTH
		)

		if not satisfies:
			raise PasswordError(f"Password does not meet the minimum requirements: {reason}")

		pwd_manager = PwdManager()
		pwd_manager.file_path = path

		salt, key = get_key_from_pwd(
			pwd=pwd,
			file_path=path
		)
		pwd_manager._key	= key
		pwd_manager._salt	= salt

		data: dict[str, str] = decrypt_data(
			key=key,
			file_path=path
		)

		try:
			for tup in data:
				website, username, description = (
					value.strip()
						for value in tup.split(",", 2)
				)

				try:
					pwd_manager.add_entry(
						website=website,
						username=username,
						description=description,
						password=data[tup]
					)
				except EntryExistsError:
					# Fallback to avoid data loss
					while True:
						random = rand.randint(1, 1000)
						website = website + f"_dup_{random}"
						try:
							pwd_manager.add_entry(
								website=website,
								username=username,
								description=description,
								password=data[tup]
							)
							break
						except EntryExistsError:
							continue

		except (
			KeyError,
			TypeError,
			ValueError
		) as e:
			raise VaultFormatError from e

		return pwd_manager

	"""
		creates a PwdManager object and initializes the vault file
		@raises:
			- FileNotFoundError(path) [OSError]
			- KeyLengthError
			- KeyDerivationError
			- OSError
	"""
	@staticmethod
	def _pwd_manager_from_pwd(
		path	: str,
		pwd		: str
	) -> PwdManager:
		salt, key = derive_key(pwd)

		pwd_manager = PwdManager(
			path=path,
			key=key,
			salt=salt
		)

		pwd_manager.encrypt()

		return pwd_manager

	@staticmethod
	def _pwd_satisfies_conditions(pwd: str, len_min=PWD_LENGTH) -> tuple[bool, str]:
		if len(pwd) < len_min:
			return False, f'must be at least {len_min} characters long'

		for digit in DIGITS:
			if digit in pwd:
				break
		else:
			return False, 'must contain at least one digit'

		for letter in LETTERS_LOWER:
			if letter in pwd:
				break
		else:
			return False, 'must contain at least one lowercase character'

		for letter in LETTERS_UPPER:
			if letter in pwd:
				break
		else:
			return False, 'must contain at least one uppercase character'

		for spec in SPECIAL_CHARS:
			if spec in pwd:
				break
		else:
			return False, 'must contain at least one special character'

		return True, ''

	@staticmethod
	def _has_new_format(data: object) -> bool:
		return 	isinstance(data, dict) 	\
			and all(
					isinstance(key, str)
					and len(key.split(",", 2)) == 3
					and isinstance(value, dict)
					and isinstance(value.get(PWD), str)
					and isinstance(value.get(TOTP_URI), str)
						for key, value in data.items()
				)

	@staticmethod
	def _has_old_format(data: object) -> bool:
		return isinstance(data, dict) 	\
			and all(
					isinstance(key, str)
					and len(key.split(",", 2)) == 3
					and isinstance(value, str)
						for key, value in data.items()
				)