class VaultEntry(MDListItem):
	def __init__(self, name="", *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Add text to label
		self.ids.vault_name.text = name

		self.vault_name = name

class VaultList(MDScrollView):
		def add_vault(self, vault: VaultEntry):
			self.ids.vault_list.add_widget(vault)

Builder.load_file("vault_list.kv")