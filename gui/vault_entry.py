from kivy.lang.builder import Builder

from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDListItem

class VaultEntry(MDListItem):
	def __init__(self, text="", *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.ids.vault_name.text = text

class VaultList(MDScrollView):
		pass

Builder.load_file("vault_list.kv")
