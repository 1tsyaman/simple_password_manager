from threading import Thread

from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

from kivymd.uix.appbar import MDActionTopAppBarButton
from kivymd.uix.screen import MDScreen

from gui.screens.screen_manager import AppScreenManager
from gui.widgets.account_list import AccountEntry, AccountList
from gui.dialogs.login_dialog import LoginDialog
from gui.dialogs.new_account_dialog import NewAccountDialog
from gui.widgets.top_bar import TopBar
from gui.widgets.labels import NoAccountsLabel

from core.pwd_manager import PwdManager
from core.errors import EntryExistsError, KeyLengthError, log

class VaultScreen(MDScreen):
	def __init__(
		self,
		screen_manager: AppScreenManager,
		pwd_manager: PwdManager,
		*args,
		**kwargs
	):
		self.screen_manager = screen_manager
		self.pwd_manager = pwd_manager
		self.box_container = BoxLayout(
			orientation="vertical"
		)

		super().__init__(
			self.box_container,
			name="vault",
			on_pre_enter=self.refresh,
			on_enter=self.resume_loading_accounts,
			on_leave=self.clear,
			md_bg_color=self.root.theme_cls.secondaryContainerColor
			*args,
			**kwargs
		)

	"""
		Called on pre_enter
	"""
	def refresh(self):
		back_button : MDActionTopAppBarButton = self.back_button
		top_bar = self.top_bar
		dialog = self.login_dialog

		# Enable back button
		top_bar.back_callback = self.back_to_selection
		back_button.disabled = False
		back_button.opacity = 1

		# New account button
		top_bar.plus_callback = self.show_add_account_dialog

		self.changes_made = False
		self.force_exit_vault = False

		self.load_accounts(dialog=dialog)

	"""
		Called on leave
	"""
	def clear(self):
		# Cancel loading if we quit while loading wasn't finished
		if hasattr(self, "account_load_event"):
			self.account_load_event.cancel()

		self.box_container.clear_widgets()
		self.box_container.add_widget(NoAccountsLabel())

	def load_accounts(self, dialog: LoginDialog):
		self.account_list : AccountList = AccountList()

		accounts = self.pwd_manager.get_website_username_list()
		self.number_accounts = len(accounts)	# store number of accounts
		self.account_iterator = iter(accounts)	# create an iterator

		# Case: No accounts to load
		if self.number_accounts == 0:
			self.vault_screen_box.clear_widgets()
			self.vault_screen_box.add_widget(NoAccountsLabel())

			dialog.dismiss()
			return

		# Otherwise, load accounts in batches to keep UI responsive
		"""
			Function signature:
				Clock.schedule_interval(self, callback(self, dt: float) -> bool, intervall in sec)
		"""
		self._load_account_batch(dialog=dialog)

	def _load_account_batch(
			self,
			dialog: LoginDialog | None = None	# is only needed for the first batch
		) -> bool:
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

		# only switch the screen *once*, after one batch is added
		if self.screen_manager.current != "vault":
			container : BoxLayout = self.box_container
			container.clear_widgets()
			container.add_widget(self.account_list)

			if dialog is not None:
				dialog.dismiss()

			# stop loading while transitioning screens
			return False

		# if done = True, we return False -> don't schedule again
		return not done	

	"""
		Called on enter: Resumes loading the entries after screen has loaded
	"""
	def resume_loading_accounts(self):
		if self.number_accounts != 0:
			self.account_load_event =	Clock.schedule_interval(
											lambda _: self._load_account_batch(),
											0
										)

	def show_add_account_dialog(self):
		NewAccountDialog(add_account_callback=self.add_account).open()


	def add_account(
			self,
			dialog: NewAccountDialog,
			website: str,
			username: str,
			password: str,
			description: str
		):
		try:
			self.pwd_manager.add_entry(
				website=website,
				username=username,
				password=password,
				description=description
			)
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

		self.sync_thread = Thread(
			target=self.sync_pwd_manager,
			kwargs={"on_exit": False},
			daemon=False	# daemon=False -> program will not exit until thread returns
		)
		self.sync_thread.start()

		dialog.dismiss()

	def sync_pwd_manager(self, on_exit: bool = False) -> bool:
		if not self.changes_made:
			return True

		try:
			self.pwd_manager.encrypt()
			self.changes_made = False	# need to introduce locks here
			return True

		except FileNotFoundError as e:
			reason = "Vault file does not exist"
		except KeyLengthError:
			reason = "Password did not produce correct key length, contact developer"
		except OverflowError:
			reason = "Encryption failed"
		except OSError as e:
			reason = "Something went wrong, check log"
			log(
				message=reason,
				error=e
			)

		kwargs = {
					"error_title": "Error: Changes not saved",
					"error_message": reason,
					"first_button_label": "Dismiss",
					"first_button_callback": lambda dialog: dialog.dismiss(),
				}

		if on_exit:
			kwargs["second_button_label"]		= "Exit anyways"
			kwargs["second_button_callback"]	= self.screen_manager.force_exist_vault_screen

		# because UI work should only happen on the main thread
		Clock.schedule_once(
			lambda _: self.show_error_dialog(kwargs=kwargs),
			0
		)
		return False