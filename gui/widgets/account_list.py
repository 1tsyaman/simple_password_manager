from collections.abc import Callable

from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import (
	MDListItem,
	MDListItemLeadingIcon,
	MDListItemHeadlineText,
	MDListItemSupportingText
)

class AccountEntry(MDListItem):
	def __init__(
		self,
		website: str,
		username: str,
		on_click_callback: Callable,	# on_click(instance: AccountEntry)
		*args,
		**kwargs
	):
		self.website_label = MDListItemHeadlineText(
								text=website
							)
		self.username_label = MDListItemSupportingText(
								text=username
							)

		super().__init__(
			MDListItemLeadingIcon(
				icon="account"
			),

			self.website_label,
			self.username_label,

			pos_hint={
				"center_x": 0.5,
				"center_y": 0.5
			},

			on_release=on_click_callback,
			*args,
			**kwargs
		)

		self.website = website
		self.username = username

	def update_labels(
		self,
		website: str,
		username: str
	):
		self.website_label.text = website
		self.username_label.text = username

		self.website = website
		self.username = username


class AccountList(MDScrollView):
	def __init__(self, *args, **kwargs):
		self.account_list = MDBoxLayout(
			orientation="vertical",
			adaptive_height=True,
			spacing="8dp",
			padding="4dp",
		)

		super().__init__(
			self.account_list,
			do_scroll_x=False,
			*args,
			**kwargs
		)

	def add_account(self, account: AccountEntry):
		self.account_list.add_widget(account)