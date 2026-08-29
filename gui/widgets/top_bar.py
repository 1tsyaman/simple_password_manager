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
		self.title = title

		self.back_button = MDActionTopAppBarButton(
			icon="arrow-left",
			on_release=self.on_back
		)
		self.import_vault_button	= MDActionTopAppBarButton(
			icon="file-import",
			on_release=self.on_import
		)
		self.settings_button		= MDActionTopAppBarButton(
			icon="cog"
		)

		self._back_button_container = MDTopAppBarLeadingButtonContainer(
			self.back_button
		)
		self._back_button_is_on = True	# internal state

		self.title_widget = MDTopAppBarTitle(
			text="Password Manager",
			theme_font_size="Custom",
			font_size=sp(17),
		)

		# indirect callback for the buttons (to avoid binding and unbinding buttons)
		self.back_callback		: Callable | None = None
		self.import_callback	: Callable | None = None

		super().__init__(
			self._back_button_container,

			self.title_widget,

			MDTopAppBarTrailingButtonContainer(
				self.import_vault_button,
				self.settings_button
			),

			type="small",
			*args,
			**kwargs
		)

	def on_back(self, instance=None):
		if self.back_callback is not None:
			self.back_callback()

	def on_import(self, instance=None):
		if self.import_callback is not None:
			self.import_callback()

	def remove_back_button(self):
		if self._back_button_is_on:
			self._back_button_container.clear_widgets()
			self._back_button_is_on = False

	def add_back_button(
		self,
		callback: Callable
	):
		if not self._back_button_is_on:
			self._back_button_container.add_widget(self.back_button)
			self.back_callback = callback
			self._back_button_is_on = True

	"""
		Resets the title to the defautl APP_NAME
	"""
	def reset_title(self):
		self.title_widget.text = self.title

	def set_title(
		self,
		title: str,
	):
		self.title_widget.text = title

	def clear_title(self):
		self.title_widget.text = ""
