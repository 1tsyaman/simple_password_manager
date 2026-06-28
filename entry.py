from __future__ import annotations

class Entry:
	def __init__(self):
		self.website		= ""
		self.username           = ""
		self.description        = ""

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
	
	"""
		This function ignores the description
	"""
	def is_equal(self: Entry, other: Entry) -> bool:
		return self.website.strip().lower() == other.website.strip().lower() \
			and self.username.strip().lower() == other.username.strip().lower()
	


	@staticmethod
	def create_entry(website: str, username: str, description=""):
		entry = Entry()

		entry.website		= website
		entry.username		= username
		entry.description	= description

		return entry

	@staticmethod
	def from_json(entry: dict[str, str]):
		return Entry.create_entry(entry["website"], entry["username"], entry["description"])