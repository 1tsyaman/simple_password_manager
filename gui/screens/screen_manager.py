from kivymd.uix.screenmanager import MDScreenManager

class AppScreenManager(MDScreenManager):
	def switch_screen(self, screen: str, on_exit: bool = False):
		if screen in ["selection", "vault"] \
			and (
					self.screen_manager.current != "vault"
					or self.vault_screen_can_switch(on_exit=on_exit)	# current = vault? -> check if we can exit
				):
				self.screen_manager.current = screen

	def vault_screen_can_switch(self, on_exit: bool = False):
		return self.force_exit_vault \
				or (not self.changes_made or self.sync_pwd_manager(on_exit=on_exit))	# changes made -> sync

	def force_exist_vault_screen(self, dialog: ErrorDialog):
		dialog.dismiss()
		self.force_exit_vault = True
		self.switch_screen("selection", on_exit=True)