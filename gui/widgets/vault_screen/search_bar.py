from collections.abc import Callable

from kivy.metrics import dp
from kivy.uix.widget import Widget

from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.recycleboxlayout import MDRecycleBoxLayout
from kivymd.uix.search import (
	MDSearchBar,
	MDSearchBarLeadingContainer,
	MDSearchLeadingIcon,
	MDSearchBarTrailingContainer,
	MDSearchViewLeadingContainer,
	MDSearchViewContainer,
	MDSearchViewTrailingContainer,
	MDSearchTrailingIcon
)

from gui.widgets.vault_screen.account_list import AccountEntry

class SearchBar(MDSearchBar):
	"""
		search_function returns a list of dicts of the following shape:
			{
				""viewclass": "SomeWidget",
				... widget-specific args...,
				"callback":		some_handler
			}
	"""
	def __init__(
		self,
		view_root: Widget,
		search_function: Callable[[str], list[dict]],
		leading_button_icon: str = "",
		leading_button_callback: Callable | None = None,	# What the back button should do in search is not engaged
		search_text: str = "Search",
		trailing_button_icon: str = "",
		trailing_button_callback: Callable | None = None,
		*args,
		**kwargs
	):
		self.search_function = search_function
		self.leading_button_callback = leading_button_callback
		self.trailing_button_callback = trailing_button_callback

		self.recycle_layout = MDRecycleBoxLayout(
			orientation="vertical",
			default_size=(None, dp(72)),
			default_size_hint=(1, None),
			adaptive_height=True,
			spacing="8dp",
			padding="4dp",
		)

		self.recycle_view = MDRecycleView(
			self.recycle_layout
		)

		self.recycle_view.key_viewclass = "viewclass"
		self.recycle_view.key_size = "height"

		super().__init__(
			# Main view
			MDSearchBarLeadingContainer(
				MDSearchLeadingIcon(
					icon=leading_button_icon,
					on_release=lambda *_: self._leading_button_callback()
				),
			),

			MDSearchBarTrailingContainer(
				MDSearchTrailingIcon(
					icon=trailing_button_icon,
					on_release=lambda *args: self._trailing_button_callback(*args)
				)
			),

			# Search view (Bar)
			MDSearchViewLeadingContainer(
				MDSearchLeadingIcon(
					icon="arrow-left",
					on_release=lambda *_: self.close_view()
				)
			),

			MDSearchViewTrailingContainer(
				MDSearchTrailingIcon(
					icon="window-close",
					on_release=lambda *_: setattr(self, "text", "")
				)
			),

			# Search view (main)
			MDSearchViewContainer(
				self.recycle_view,
			),

			*args,
			**kwargs
		)

		self.supporting_text = search_text
		self.view_root = view_root
		self.bind(text=lambda _, value: self._handle_search(value))

	"""
		Should be called before removing a SearchBar widget
	"""
	def detach(self):
		widget = self._search_widget

		if widget:
			widget.parent.remove_widget(widget)

	def close_view(self) -> None:
		self.text = ""
		return super().close_view()

	def _leading_button_callback(self):
		if self.leading_button_callback is not None:
			self.leading_button_callback()

	def _trailing_button_callback(self, *args):
		if self.trailing_button_callback is not None:
			self.trailing_button_callback(*args)

	def _handle_search(self, text: str):
		self.recycle_view.data = self.search_function(text)