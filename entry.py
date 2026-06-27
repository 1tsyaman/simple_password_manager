class Entry:
	def __init__(self):
		self.username           = ""
		self.password           = ""
		self.description        = ""

	def get_json(self):
		obj = {
			"username":	self.username,
			"password":	self.password,
			"description":	self.description
		}

		return obj
	
	def get_username(self) -> str:
		return self.username

	def get_password(self) -> str:
		return self.password

	def get_description(self) -> str:
		return self.description

	@staticmethod
	def create_entry(username: str, password: str, description: str):
		entry = Entry()

		entry.username = username
		entry.password = password
		entry.description = description

		return entry

	@staticmethod
	def from_json(entry: dict[str, str]):
		return Entry.create_entry(entry["username"], entry["password"], entry["description"])
