from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager

from kivymd.app import MDApp
from kivymd.uix.appbar import MDTopAppBar
from kivymd.uix.screen import MDScreen


from gui.selection_screen import SelectionScreen
from gui.vault_entry import VaultEntry, VaultList
from gui.login import LoginDialog
import storage.io as io

def init_app():
	Builder.load_file("top_bar.kv")

class TopBar(MDTopAppBar):
	pass


class SimplePasswordManagerApp(MDApp):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.app_data_path = str(io.get_app_data_path())
		self.vaults = io.get_vault_list(self.app_data_path)

	def load_vault_entries(self):
		if len(self.vaults) == 0:
			return

		screen_manager : ScreenManager 	= self.root.ids.screen_manager
		old_selection_screen : MDScreen 	= screen_manager.get_screen("selection")
		vault_list : VaultList 				= VaultList()

		for vault in self.vaults:
			entry = VaultEntry(name=vault)
			entry.bind(on_release=self.open_vault_decrypt_dialog)

			vault_list.add_widget(entry)

		new_selection_screen = SelectionScreen()
		new_selection_screen.add_widget(vault_list)

		screen_manager.remove_widget(old_selection_screen)
		screen_manager.add_widget(new_selection_screen)


	# Bound to vault entries
	def open_vault_decrypt_dialog(self, instance: VaultEntry) -> None:
		self.login_dialog = LoginDialog(vault=instance.vault_name, callback=self.open_vault)
		self.login_dialog.open()

	def open_vault(self, vault_name: str, password: str):
		print(f"Openning vault with name {vault_name} and password {password}")

	def on_start(self):
		self.load_vault_entries()

	# Should return the main widget, the selection screen in this case.
	def build(self):
		# Init top bar
		init_app()
		return Builder.load_file("main.kv")

if __name__ == "__main__":
	SimplePasswordManagerApp().run()