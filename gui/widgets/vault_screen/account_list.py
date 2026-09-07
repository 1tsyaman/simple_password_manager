from collections.abc import Callable

from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp

from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.recycleboxlayout import MDRecycleBoxLayout
from kivymd.uix.list import (
	MDListItem,
	MDListItemLeadingIcon,
	MDListItemHeadlineText,
	MDListItemSupportingText
)

class AccountEntry(MDListItem):
	"""
		We make the attributes Kivy properties to be able to react to changes
		in their values.
		Changing a Kivy property is an event, to which we can bind a callback.

		Kivy Properties have generic getter/setter methods
		Check out: https://kivy.org/doc/stable/api-kivy.properties.html
	"""
	website				= StringProperty("")
	username			= StringProperty("")
	on_click_callback	= ObjectProperty(None, allownone=True)

	def __init__(
		self,
		*args,
		**kwargs
	):
		self.website_label = MDListItemHeadlineText()
		self.username_label = MDListItemSupportingText()

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
			*args,
			**kwargs
		)

		"""
			A callback of a Kivy property has the signature
				callback(instance: AccountEntry, value: str)
			instance is the object that changed, not the attribute itself
		"""
		self.bind(
			website=lambda _, value: setattr(self.website_label, "text", value),
			username=lambda _, value: setattr(self.username_label, "text", value),
			on_release=self._on_release
		)

	def _on_release(self, _):
		if self.on_click_callback is not None:
			self.on_click_callback(self)


class AccountList(MDRecycleView):
	def __init__(self, *args, **kwargs):
		self.layout = MDRecycleBoxLayout(
			orientation="vertical",
			default_size=(None, dp(72)),
			default_size_hint=(1, None),
			adaptive_height=True,
			spacing="8dp",
			padding="4dp",
		)

		super().__init__(
			self.layout,
			do_scroll_x=False,
			*args,
			**kwargs
		)

		self.viewclass = AccountEntry

	def add_account(
			self,
			website: str,
			username: str,
			on_click_callback: Callable		# on_click_callback(instance: AccountEntry)
		):
		# Append to the data list
		self.data.append(
			{
				"website": 				website,
				"username":				username,
				"on_click_callback":	on_click_callback
			}
		)

	def update_account(
		self,
		old_website: str,
		old_username: str,
		new_website: str,
		new_username: str
	):
		data = self.data
		index = self._get_index(
			website=old_website,
			username=old_username
		)

		data[index]["website"]	= new_website
		data[index]["username"] = new_username

		self.data = data	# update the whole list to trigger a visual change

	def remove_account(
			self,
			website: str,
			username: str
		):
		try:
			index = self._get_index(
				website=website,
				username=username
			)
		except IndexError:
			return

		self.data.pop(index)


	"""
		@raises:
			- IndexError
	"""
	def _get_index(
			self,
			website: str,
			username: str
	) -> int:
		for i, dic in enumerate(self.data):
			if 	dic["website"] == website	\
			and dic["username"] == username:
				return i

		raise IndexError
