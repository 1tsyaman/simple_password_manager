from __future__ import annotations
from core.totp import TOTP_Config
from core.errors import (
	EntryHasNoTotp,
	InvalidEntryJSON
)

class Entry:
	def __init__(self):
		self.website	 : str					= ""
		self.username    : str       			= ""
		self.description : str       			= ""
		self.totp_config : TOTP_Config | None	= None

####	Getters		####

	def get_website(self: Entry) -> str:
		return self.website

	def get_username(self: Entry) -> str:
		return self.username

	def get_description(self: Entry) -> str:
		return self.description

	"""
		@raises:
			- EntryHasNoTotp
	"""
	def get_totp_config(self: Entry) -> TOTP_Config:
		if self.totp_config is not None:
			return self.totp_config

		raise EntryHasNoTotp

####	Setters		####

	def set_website(
		self: Entry,
		website: str
	):
		self.website = website
	
	def set_username(
		self: Entry,
		username: str
	):
		self.username = username
	
	def set_description(
		self: Entry,
		description: str
	):
		self.description = description
	
	def set_totp_config(
		self: Entry,
		totp_config: TOTP_Config | None
	):
		self.totp_config = totp_config

####	Boolean methods		####

	def has_totp(self: Entry) -> bool:
		return self.totp_config is not None

	"""
		This function ignores the description
	"""
	def is_equal(
		self: Entry,
		other: Entry
	) -> bool:
		return self.website.strip().lower() == other.website.strip().lower() \
			and self.username.strip().lower() == other.username.strip().lower()

####	Formating methods		####

	"""
		returns a string "('website', 'username')"
	"""
	def get_website_username_pair_string(self: Entry) -> str:
		return f"({self.website}, {self.username})"

	"""
		returns a string
			"
				Website: 'website'
				Username: 'username'
				Description: 'description'
			"
	"""
	def get_formatted_entry_string(self: Entry) -> str:
		return	f"Website: {self.website}\n"		\
			+	f"Username: {self.username}\n"		\
			+	f"Description: {self.description}"

	def get_json(self: Entry):
		obj = {
			"website":		self.website,
			"username":		self.username,
			"description":	self.description,
			"totp_config":	self.totp_config.to_json()
								if self.totp_config is not None
								else {}
		}

		return obj

#### 	Statics		####

	@staticmethod
	def create_entry(
		website: str,
		username: str,
		description: str = "",
		totp_config: TOTP_Config | None = None
	):
		entry = Entry()

		entry.website		= website
		entry.username		= username
		entry.description	= description
		entry.totp_config	= totp_config

		return entry

	"""
		entry: {
			"website":		"Facebook",
			"username":		"sample_user",
			"description":	"sample_desc"
		}

		@raises:
			- InvalidEntryJSON
	"""
	@staticmethod
	def from_json(entry: dict) -> Entry:
		try:
			website		= entry["website"]
			username	= entry["username"]
			description	= entry["description"]

			if not all(
				isinstance(value, str)
					for value in [website, username, description]
			):
				raise InvalidEntryJSON

			return Entry.create_entry(
				website=website,
				username=username,
			    description=description
			)

		except (KeyError, TypeError):
			raise InvalidEntryJSON