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

Builder.load_file("account_list.kv")