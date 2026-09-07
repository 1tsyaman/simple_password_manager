from collections.abc import Callable

from kivy.metrics import sp

from kivymd.uix.appbar import (
	MDTopAppBar,
	MDTopAppBarTitle,
	MDActionTopAppBarButton,
	MDTopAppBarLeadingButtonContainer,
	MDTopAppBarTrailingButtonContainer
)

class TopBar(MDTopAppBar):
	def __init__(
		self,
		title: str,
		*args,
		**kwargs
	):
		self.leading_button_container	= MDTopAppBarLeadingButtonContainer()
		self.trailing_buttons_container	= MDTopAppBarTrailingButtonContainer()

		self.title_widget = MDTopAppBarTitle(
			text=title,
			theme_font_size="Custom",
			font_size=sp(17),
		)

		super().__init__(
			self.leading_button_container,
			self.title_widget,
			self.trailing_buttons_container,
			type="small",
			*args,
			**kwargs
		)

class SettingsScreenTopBar(TopBar):
	def __init__(
		self,
		back_callback: Callable,
		*args,
		**kwargs
	):
		super().__init__(
			title="Settings",
			*args,
			**kwargs
		)

		back_button = MDActionTopAppBarButton(
			icon="arrow-left",
			on_release=lambda *_: back_callback()
		)

		self.leading_button_container.add_widget(back_button)