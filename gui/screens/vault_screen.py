from threading import Thread, Lock
from typing import TYPE_CHECKING, Any

from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from gui.dialogs.login_dialog import LoginDialog
from gui.dialogs.new_account_dialog import NewAccountDialog
from gui.dialogs.account_details_dialog import AccountDetailsDialog
from gui.widgets.account_list import AccountEntry, AccountList
from gui.widgets.labels import NoAccountsLabel
from gui.widgets.search_bar import SearchBar
from gui.utils.clipboard import copy_text

from core.pwd_manager import PwdManager
from core.errors import (
	EntryExistsError,
	KeyLengthError,
	NoSuchEntryError,
	EntryHasNoTotp,
	log
)

BATCH_SIZE = 100

# to avoid cicular import issues
if TYPE_CHECKING:
	from gui.screens.screen_manager import AppScreenManager

class VaultScreen(MDScreen):
	def __init__(
		self,
		app_data_path: str,
		phone_screen: MDScreen,
		screen_manager: "AppScreenManager",	# forward reference for type checking
		pwd_manager: PwdManager,
		*args,
		**kwargs
	):
		self.app_data_path = app_data_path
		self.phone_screen = phone_screen
		self.screen_manager = screen_manager
		self.pwd_manager = pwd_manager
		self.vault_name = ""

		"""
			Guards self.pwd_manager from being modified concurrently
				- Used by self.sync_pwd_manager to create a sound copy of the password manager
					for encryption
		"""
		self.pwd_manager_lock = Lock()

		"""
			Guards self.sync_pwd_manager() calls
			- Prevents two sync threads from creating an inconsistent vault state
		"""
		self.sync_lock = Lock()

		"""
			Locking mechanism to prevent changes made while an asynchronous
				sync thread is already running from being ignored
			
			- Whenever changes are made: Acquire lock -> self.change_version += 1
			- Sync thread aquires lock	-> stores the version -> actually syncs
										-> acquires the lock again
										-> only sets self.synced_verion = self.change_verion
											if the change version did not change during this sync operation
											since otherwise another sync thread has been queued.
		"""
		self.change_lock = Lock()
		self.change_version = 0
		self.synced_version = 0

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
			name="vault",
			md_bg_color=app.theme_cls.secondaryContainerColor,
			*args,
			**kwargs
		)

	def on_pre_enter(self, *args):
		self.refresh()

	"""
		Called on pre_enter
	"""
	def refresh(self):
		dialog = self.login_dialog

		search_bar = SearchBar(
			view_root=self.phone_screen,
			search_function=self.search_accounts,
			search_text="Search accounts...",
			leading_button_icon="arrow-left",
			leading_button_callback=self.screen_manager.back_to_selection,
			trailing_button_icon="dots-vertical",
			trailing_button_callback=None,		# TODO: Add drop down menu for this
		)

		self.screen_manager.switch_top_bar(
			search_bar,
			padding="2dp"
		)

#		top_bar.add_back_button(
#			callback=self.screen_manager.back_to_selection
#		)
#		top_bar.set_title(self.vault_name)
#
#		# Disable import button
#		top_bar.import_callback = None
#		import_button.disabled = True
#		import_button.opacity = 0
#
#		# New account button
#		top_bar.plus_callback = self.show_add_account_dialog

		with self.change_lock:
			self.change_version = 0
			self.synced_version = 0

		self.force_exit_vault = False

		self.load_accounts(dialog=dialog)

	def on_back(self):
		self.screen_manager.back_to_selection()

	def on_leave(self, *args):
		self.clear()

	"""
		Called on leave
	"""
	def clear(self):
		# Cancel loading if we quit while loading wasn't finished
		if hasattr(self, "account_load_event"):
			self.account_load_event.cancel()

		self.clear_widgets()
		self.add_widget(NoAccountsLabel())

	def load_accounts(self, dialog: LoginDialog):
		self.account_list : AccountList = AccountList()

		accounts = self.pwd_manager.get_website_username_pair_list()
		self.number_accounts = len(accounts)	# store number of accounts
		self.account_iterator = iter(accounts)	# create an iterator

		# Case: No accounts to load
		if self.number_accounts == 0:
			self.clear_widgets()
			self.add_widget(NoAccountsLabel())

			dialog.dismiss()
			return

		# Otherwise, load accounts in batches to keep UI responsive
		"""
			Function signature:
				Clock.schedule_interval(self, callback(self, dt: float) -> bool, intervall in sec)
		"""
		self._load_account_batch(dialog=dialog, first_batch=True)

	def _load_account_batch(
			self,
			dialog: LoginDialog | None = None,	# is only needed for the first batch
			first_batch: bool = False
		) -> bool:
		batch_size = min(BATCH_SIZE, self.number_accounts)
		done = False

		# Add accounts in batches of 10
		for _ in range(batch_size):
			try:
				website, username = next(self.account_iterator)

			# Whenever we're done
			except StopIteration:
				done = True
				break

			self.account_list.add_account(
				website=website,
				username=username,
				on_click_callback=self.show_account_details_dialog
			)

		# only switch the screen *once*, after one batch is added
		if first_batch:
			self.clear_widgets()
			self.add_widget(self.account_list)

			if dialog is not None:
				dialog.dismiss()

			# stop loading while transitioning screens
			return False

		# if done = True, we return False -> don't schedule again
		return not done	

	def on_enter(self, *args):
		self.resume_loading_accounts()

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

	"""
		Adds the account and starts an *asynchronous* thread to sync vault
	"""
	def add_account(
			self,
			dialog: NewAccountDialog,
			website: str,
			username: str,
			password: str,
			description: str
		):
		try:
			# Lock the pwd_manager before modifying it
			with self.pwd_manager_lock:
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

		self.account_list.add_account(
			website=website,
			username=username,
			on_click_callback=self.show_account_details_dialog
		)

		if self.number_accounts == 0:
			self.clear_widgets()
			self.add_widget(self.account_list)

		with self.change_lock:
			self.change_version += 1

		Thread(
			target=self.sync_pwd_manager,
			kwargs={"on_exit": False},
			daemon=False	# daemon=False -> program will not exit until thread returns
		).start()

		dialog.dismiss()

	def show_account_details_dialog(self, instance: AccountEntry):
		website = instance.website
		username = instance.username

		try:
			password_desc = self.pwd_manager.get_password_and_description(
				website=website,
				username=username
			)
		except NoSuchEntryError:
			# Emit error!
			return

		password = password_desc["password"]
		description = password_desc["description"]

		kwargs = {
			"website":			website,
			"username":			username,
			"password":			password,
			"description":		description,
			"copy_callback":		copy_text,
			"modify_callback":	self.modify_account_details,
			"delete_callback":	self.delete_account,
			"account_entry":		instance,
		}

		try:
			totp_code, time_remaining = self.pwd_manager.get_totp(website=website, username=username)
			kwargs["totp_code"] = totp_code
			kwargs["totp_time_remaining"] = time_remaining
			kwargs["totp_callback"] = self.pwd_manager.get_totp
		except NoSuchEntryError:
			self.screen_manager.show_error_dialog(
				error_title="Error: Inconsistent internal state",
				error_message="Selected entry does not exist",
			)
			return
		except EntryHasNoTotp:
			pass	# No TOTP, no problem

		AccountDetailsDialog(
			**kwargs
		).open()

	"""
		Updates the internal state and starts an *asynchronous* thread to sync vault
	"""
	def modify_account_details(
		self,
		website: str,
		username: str,
		new_website: str,
		new_username: str,
		new_password: str,
		new_description: str,
		account_entry: AccountEntry,
	) -> bool:
		try:
			with self.pwd_manager_lock:
				self.pwd_manager.update_entry(
					website=website,
					username=username,
					new_website=new_website,
					new_username=new_username,
					new_password=new_password,
					new_description=new_description
				)
		except NoSuchEntryError:
			self.screen_manager.show_error_dialog(
				error_title="Error: Changes not saved",
				error_message="Vault state is inconsistent: Modified entry does not exist!"
			)
			return False

		self.account_list.update_account(
			old_website=website,
			old_username=username,
			new_website=new_website,
			new_username=new_username
		)

		with self.change_lock:
			self.change_version += 1

		Thread(
			target=self.sync_pwd_manager,
			kwargs={"on_exit": False},
			daemon=False	# daemon=False -> program will not exit until thread returns
		).start()

		return True

	"""
		Deletes the account and starts an *asynchronous* thread to sync vault
	"""
	def delete_account(
		self,
		website: str,
		username: str,
		account_entry: AccountEntry,
	):
		with self.pwd_manager_lock:
			self.pwd_manager.remove_entry(
				website=website,
				username=username
			)

		self.account_list.remove_account(
				website=website,
				username=username
		)

		with self.change_lock:
			self.change_version += 1

		Thread(
			target=self.sync_pwd_manager,
			kwargs={"on_exit": False},
			daemon=False	# daemon=False -> program will not exit until thread returns
		).start()

	def search_accounts(
		self,
		query: str
	) -> list[dict[str, Any]]:
		return []

	"""
		Creates a snapshot of the current state of self.pwd_manager and encrypts it.
			- Acquires self.sync_lock.
	"""
	def sync_pwd_manager(
		self,
		on_exit: bool = False,
		error_dialog: bool = True,
	) -> bool:
		with self.sync_lock:

			with self.change_lock:
				if self.change_version == self.synced_version:
					return True

				version = self.change_version

			# Create a snap shot of the current state
			with self.pwd_manager_lock:
				pwd_manager = self.pwd_manager.get_snapshot()

			try:
				# Encrypt the snapshot
				pwd_manager.encrypt()

				# Update the synced version
				with self.change_lock:
					self.synced_version = version

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

			# Only show error dialog if requested
			if not error_dialog:
				return False

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
			lambda _: self.screen_manager.show_error_dialog(**kwargs),
			0
		)
		return False