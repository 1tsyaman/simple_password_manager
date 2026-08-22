from threading import Thread
from typing import TYPE_CHECKING

from kivymd.uix.boxlayout import MDBoxLayout
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.appbar import MDActionTopAppBarButton
from kivymd.uix.screen import MDScreen

from gui.dialogs.login_dialog import LoginDialog
from gui.dialogs.new_account_dialog import NewAccountDialog
from gui.dialogs.account_details_dialog import AccountDetailsDialog
from gui.widgets.account_list import AccountEntry, AccountList
from gui.widgets.labels import NoAccountsLabel
from gui.widgets.top_bar import TopBar
from gui.utils.clipboard import copy_text

from core.pwd_manager import PwdManager
from core.errors import (
	EntryExistsError,
	KeyLengthError,
	NoSuchEntryError,
	log
)

# to avoid cicular import issues
if TYPE_CHECKING:
	from gui.screens.screen_manager import AppScreenManager

class VaultScreen(MDScreen):
	def __init__(
		self,
		app_data_path: str,
		screen_manager: "AppScreenManager",	# forward reference for type checking
		pwd_manager: PwdManager,
		top_bar: TopBar,
		*args,
		**kwargs
	):
		self.app_data_path = app_data_path
		self.screen_manager = screen_manager
		self.pwd_manager = pwd_manager
		self.top_bar = top_bar

		self.box_container = MDBoxLayout(
			orientation="vertical"
		)

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
			self.box_container,
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
		top_bar = self.top_bar
		back_button : MDActionTopAppBarButton = top_bar.back_button
		import_button: MDActionTopAppBarButton = top_bar.import_vault_button

		dialog = self.login_dialog

		# Enable back button
		top_bar.back_callback = self.screen_manager.back_to_selection
		back_button.disabled = False
		back_button.opacity = 1

		# Disable import button
		top_bar.import_callback = None
		import_button.disabled = True
		import_button.opacity = 0

		# New account button
		top_bar.plus_callback = self.show_add_account_dialog

		self.changes_made = False
		self.force_exit_vault = False

		self.load_accounts(dialog=dialog)

	def on_leave(self, *args):
		self.clear()

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
			self.box_container.clear_widgets()
			self.box_container.add_widget(NoAccountsLabel())

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

			entry = AccountEntry(
				website=website,
				username=username,
				on_click_callback=self.show_account_details_dialog
			)
			self.account_list.add_account(entry)

		# only switch the screen *once*, after one batch is added
		if first_batch:
			container : MDBoxLayout = self.box_container
			container.clear_widgets()
			container.add_widget(self.account_list)

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
		entry = AccountEntry(
			website=website,
			username=username,
			on_click_callback=self.show_account_details_dialog
		)
		self.account_list.add_account(entry)

		if self.number_accounts == 0:
			container : MDBoxLayout = self.box_container
			container.clear_widgets()
			container.add_widget(self.account_list)

		self.changes_made = True

		self.sync_thread = Thread(
			target=self.sync_pwd_manager,
			kwargs={"on_exit": False},
			daemon=False	# daemon=False -> program will not exit until thread returns
		)
		self.sync_thread.start()

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
			"account_entry":		instance,
		}

		try:
			totp_code, time_remaining = self.pwd_manager.get_totp(website=website, username=username)
			kwargs["totp_code"] = totp_code
			kwargs["totp_time_remaining"] = time_remaining
			kwargs["totp_callback"] = self.pwd_manager.get_totp
		except:
			# TODO: emit eroor!
			pass

		AccountDetailsDialog(
			**kwargs
		).open()

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
			self.pwd_manager.update_entry(
				website=website,
				username=username,
				new_website=new_website,
				new_username=new_username,
				new_password=new_password,
				new_description=new_description
			)
		except NoSuchEntryError:
			return False

		self.changes_made = True

		account_entry.update_labels(
			website=new_website,
			username=new_username
		)

		return self.sync_pwd_manager(
			on_exit=False,
			error_dialog=False
		)

	def sync_pwd_manager(
		self,
		on_exit: bool = False,
		error_dialog: bool = True,
	) -> bool:
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
			lambda _: self.screen_manager.show_error_dialog(kwargs=kwargs),
			0
		)
		return False