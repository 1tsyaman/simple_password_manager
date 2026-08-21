from kivymd.uix.screen import MDScreen
from kivy.lang.builder import Builder

from kivymd.uix.appbar import MDActionTopAppBarButton

from widgets.top_bar import TopBar

class SelectionScreen(MDScreen):

	def refresh(self):
		top_bar : TopBar = self.root.top_bar
		back_button : MDActionTopAppBarButton = top_bar.back_button

		# New vault button
		top_bar.plus_callback = self.show_new_vault_dialog

		# Disable back button
		top_bar.back_callback = None
		back_button.disabled = True
		back_button.opacity = 0

		self.load_vaults_to_screen()

	def clear(self):
		self.selection_screen_box.clear_widgets()
		self.selection_screen_box.add_widget(NoVaultsLabel())

	def load_vaults(self):
		# refresh vault list
		self.vaults = io.get_vault_list(self.app_data_path)

		if len(self.vaults) == 0:
			# Add no_vaults_label
			self.selection_screen_box.clear_widgets()
			self.selection_screen_box.add_widget(NoVaultsLabel())
			return

		vault_list : VaultList 				= VaultList()

		for vault in self.vaults:
			entry = VaultEntry(name=vault)
			entry.bind(on_release=self.show_open_vault_dialog)

			vault_list.add_vault(entry)

		container : BoxLayout = self.selection_screen_box
		container.clear_widgets()
		container.add_widget(vault_list)

	# Bound to vault entries
	def show_open_vault_dialog(self, instance: VaultEntry) -> None:
		self.login_dialog = LoginDialog(vault=instance.vault_name, login_callback=self.open_vault)
		self.login_dialog.open()

	def open_vault(self, login_dialog: LoginDialog, vault_name: str, password: str):
		password_field : InputField = login_dialog.password_field 
		error_widget = password_field.error_widget

		try:
			self.pwd_manager = io.load_vault_for_gui(self.app_data_path, vault_name, password)
			self.load_vault_entries_to_screen(login_dialog=login_dialog)
			self.changes_made = False

		except PasswordError:
			error_widget.text = "Incorrect Password"
			password_field.error = True
		except FileNotFoundError:
			error_widget.text = f"Vault path not valid"
			password_field.error = True
		except KeyLengthError:
			error_widget.text = "Derived key has incorrect length, contact developer"
			password_field.error = True
		except KeyDerivationError:
			error_widget.text = "Failed to derive key from password"
			password_field.error = True
		except VaultFormatError:
			error_widget.text = "Vault format incorrect"
			password_field.error = True
		except CorruptedVaultError:
			error_widget.text = "Incorrect password or corrupted vault"
			password_field.error = True
		except Exception as e:
			print(f"Something went wrong while opening the vault: {e}")
			traceback.print_exc()
			error_widget.text = "Something went wrong, check log"
			password_field.error = True

	def create_vault(self, dialog: NewVaultDialog, name: str, password: str, conf_password: str):
		name_field 				: InputField = dialog.name_field
		password_field			: InputField = dialog.password_field
		confirm_password_field	: InputField = dialog.confirm_password_field

		try:
			vault_exists = io.vault_exists_for_gui(self.app_data_path, name)
		except OSError as e:
			print(f"Something went wrong while creating vault: {e}")
			name_field.error_widget.text = "Something went wrong, check log"
			name_field.error = True

			return False

		if vault_exists:
			name_field.error_widget.text = "Vault already exists"
			name_field.error = True

			return False

		if password != conf_password:
			confirm_password_field.error_widget.text = "Password does not match"
			confirm_password_field.error = True

			return False

		try:
			io.create_and_load_vault_for_gui(self.app_data_path, name, password)
			self.load_vaults_to_screen()
			return True

		except FileNotFoundError:
			name_field.error_widget.text = "Could not create vault file"
			name_field.error = True
		except PasswordRequirementsError as e:
			password_field.error_widget.text = e.reason
			password_field.error = True
		except KeyLengthError:
			password_field.error_widget.text = "Password did not produce correct key length, contact developer"
			password_field.error = True
		except KeyDerivationError:
			password_field.error_widget.text = "Key derivation failed."
			password_field.error = True
		except OverflowError as e:
			print(f"Something went wrong while creating vault: {e}")
			name_field.error_widget.text = "Encryption failed"
			name_field.error = True
		except OSError as e:
			print(f"Something went wrong while creating vault: {e}")
			name_field.error_widget.text = "Something went wrong, check log"
			name_field.error = True

		return False

	def show_new_vault_dialog(self):
		self.new_vault_dialog = NewVaultDialog(create_vault_callback=self.create_vault)
		self.new_vault_dialog.open()

Builder.load_file("selection_screen.kv")