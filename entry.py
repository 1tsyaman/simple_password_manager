class Entry:
        def __init__(self):
                self.website            = ""
                self.username           = ""
                self.password           = ""
                self.description        = ""

        def get_json(self):
                obj = {
                        "website":	self.website,
                        "username":	self.username,
                        "password":	self.password,
                        "description":	self.description
                }

                return obj

        @staticmethod
        def create_entry(website: str, username: str, password: str, description: str):
                entry = Entry()

                entry.website = website
                entry.username = username
                entry.password = password
                entry.description = description

                return entry