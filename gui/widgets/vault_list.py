from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import (
	MDListItem,
	MDListItemLeadingIcon,
	MDListItemHeadlineText
)

class VaultEntry(MDListItem):
	def __init__(self,
		name: str,
		*args,
		**kwargs
	):
		self.vault_name = name

		super().__init__(
			MDListItemLeadingIcon(icon="safe"),
			MDListItemHeadlineText(text=name),
			pos_hint={
				"center_x": 0.5,
				"center_y": 0.5
			},
			size_hint_min_y=0.5,
			*args,
			**kwargs
		)

class VaultList(MDScrollView):
	def __init__(self, *args, **kwargs):
		self.vault_list = MDBoxLayout(
			orientation="vertical",
			adaptive_height=True,
			spacing="8dp",
			padding="4dp",
		)

		super().__init__(
			self.vault_list,
			do_scroll_x=False
			*args,
			**kwargs
		)

	def add_vault(self, vault: VaultEntry):
		self.vault_list.add_widget(vault)