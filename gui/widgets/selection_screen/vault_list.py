from collections.abc import Callable

from kivymd.uix.button import MDIconButton
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
		context_callback: Callable,
		*args,
		**kwargs
	):
		self.vault_name = name
		self.context_button = MDIconButton(
			icon="dots-vertical",
			pos_hint={
				"center_x": 0.5,
				"center_y": 0.5,
			},
			on_release=lambda _: context_callback(
				instance=self,
				button=self.context_button
			)
		)

		super().__init__(
			MDListItemLeadingIcon(icon="safe"),
			MDListItemHeadlineText(text=name),
			self.context_button,
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