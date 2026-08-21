from kivymd.uix.screen import MDScreen
from kivy.lang.builder import Builder

class VaultScreen(MDScreen):

	def refresh_vault_screen(self):
		top_bar : TopBar = self.top_bar
		back_button : MDActionTopAppBarButton = self.back_button

		self.force_exit_vault = False

		# New account button
		top_bar.plus_callback = self.show_add_account_dialog

		# Enable back button
		top_bar.back_callback = self.back_to_selection
		back_button.disabled = False
		back_button.opacity = 1

	def clear_vault_screen(self):
		# Cancel loading if we quit while loading wasn't finished
		if hasattr(self, "account_load_event"):
			self.account_load_event.cancel()

		self.vault_screen_box.clear_widgets()
		self.vault_screen_box.add_widget(NoAccountsLabel())

	def load_vault_entries_to_screen(self, login_dialog: LoginDialog):
#		loading_indicator : MDCircularProgressIndicator = self.login_dialog.loading_indicator
		self.account_list : AccountList = AccountList()

		accounts = self.pwd_manager.get_website_username_list()
		self.number_accounts = len(accounts)		# store number of accounts
		self.account_iterator = iter(accounts)	# create an iterator
#		loading_indicator.active = True (no longer needed)

		if self.number_accounts == 0:
			self.vault_screen_box.clear_widgets()
			self.vault_screen_box.add_widget(NoAccountsLabel())

			self.login_dialog.dismiss()

			return self.switch_screen("vault")

		# Function signature:
		# 	Clock.schedule_interval(self, callback(self, dt: float) -> bool, intervall in sec)
		self.account_load_event = Clock.schedule_interval(self._load_account_batch, 0)

	def _load_account_batch(self, dt: float) -> bool:
		batch_size = min(10, self.number_accounts)
		done = False

		# Add accounts in batches of 10
		for _ in range(batch_size):
			try:
				website, username = next(self.account_iterator)

			# Whenever we're done
			except StopIteration:
				done = True
				break

			entry = AccountEntry(website=website, username=username)
			self.account_list.add_account(entry)

		# only switch the screen once, after one batch is added
		if self.screen_manager.current != "vault":
			container : BoxLayout = self.vault_screen_box
			container.clear_widgets()
			container.add_widget(self.account_list)

			self.login_dialog.dismiss()
			self.switch_screen("vault")

			# stop loading while transitioning screens
			return False

		# if done = True, we return False -> don't schedule again
		return not done	

	"""
		Resumes loading the entries after screen has loaded
	"""
	def _resume_loading_account_batch(self):
		if self.number_accounts != 0:
			self.account_load_event = Clock.schedule_interval(self._load_account_batch, 0)

	def show_add_account_dialog(self):
		self.new_account_dialog = NewAccountDialog(add_account_callback=self.add_account)
		self.new_account_dialog.open()


	def add_account(self, dialog: NewAccountDialog, website: str, username: str, password: str, description: str):
		try:
			self.pwd_manager.add_entry(website=website, username=username, password=password, description=description)
		except EntryExistsError:
			username_field = dialog.username_field
			error_widget = username_field.error_widget

			error_widget.text = "website/username combination already exists"
			username_field.error = True
			return

		# Add account to list (without refreshing the whole list)
		entry = AccountEntry(website=website, username=username)
		self.account_list.add_account(entry)
		self.changes_made = True

		self.sync_thread = Thread(target=self.sync_pwd_manager, kwargs={"on_exit": False}, daemon=False)	# daemon=False -> program will not exit until thread returns
		self.sync_thread.start()

		dialog.dismiss()

Builder.load_file("vault_screen.kv")
