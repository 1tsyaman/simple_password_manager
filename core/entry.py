from __future__ import annotations
from core.totp import TOTP

class Entry:
	def __init__(self):
		self.website	 : str		= ""
		self.username    : str       	= ""
		self.description : str       	= ""
		self.totp_config : TOTP | None	= None

	def get_json(self: Entry):
		obj = {
			"website":	self.website,
			"username":	self.username,
			"description":	self.description
		}

		return obj

	def get_website(self: Entry) -> str:
		return self.website

	def get_username(self: Entry) -> str:
		return self.username

	def get_description(self: Entry) -> str:
		return self.description
	
	def set_website(self: Entry, website: str):
		self.website = website
	
	def set_username(self: Entry, username: str):
		self.username = username
	
	def set_description(self: Entry, description: str):
		self.description = description
	
	def set_totp_config(self: Entry, uri: str):
		self.totp_config = TOTP.from_uri(uri)

	"""
		This function ignores the description
	"""
	def is_equal(self: Entry, other: Entry) -> bool:
		return self.website.strip().lower() == other.website.strip().lower() \
			and self.username.strip().lower() == other.username.strip().lower()

	"""
		returns a string ('website', 'username')
	"""
	def to_string(self: Entry) -> str:
		return f"({self.website}, {self.username})"
	
	def to_string_with_desc(self: Entry) -> str:
		return f"Website: {self.website}\nUsername: {self.username}\nDescription: {self.description}"


	@staticmethod
	def create_entry(website: str, username: str, description="", totp_uri=""):
		entry = Entry()

		entry.website		= website
		entry.username		= username
		entry.description	= description
		entry.totp_config	= TOTP.from_uri(totp_uri)

		return entry

	@staticmethod
	def from_json(entry: dict[str, str]):
		return Entry.create_entry(entry["website"], entry["username"], entry["description"])