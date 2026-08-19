from kivy.lang.builder import Builder

from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDListItem

class VaultEntry(MDListItem):
	def __init__(self, name="", *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Add text to label
		self.ids.vault_name.text = name

		self.vault_name = name

class VaultList(MDScrollView):
		def add_vault(self, vault: VaultEntry):
			self.ids.vault_list.add_widget(vault)

class AccountEntry(MDListItem):
	def __init__(self, website: str, username: str, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.ids.website.text = website
		self.ids.username.text = username

		self.website = website
		self.username = username

class AccountList(MDScrollView):
		def add_account(self, account: AccountEntry):
			self.ids.account_list.add_widget(account)

Builder.load_file("vault_list.kv")
