from collections.abc import Callable

from kivymd.uix.appbar import (
	MDTopAppBar,
	MDTopAppBarTitle,
	MDActionTopAppBarButton,
	MDTopAppBarLeadingButtonContainer,
	MDTopAppBarTrailingButtonContainer
)

class TopBar(MDTopAppBar):
	def __init__(self, *args, **kwargs):
		self.back_button			= MDActionTopAppBarButton(
			icon="arrow-left",
			on_release=self.on_back
		)
		self.import_vault_button	= MDActionTopAppBarButton(
			icon="file-import"
		)
		self.plus_button			= MDActionTopAppBarButton(
			icon="plus",
			on_release=self.on_plus
		)
		self.settings_button		= MDActionTopAppBarButton(
			icon="cog"
		)

		# indirect callback for the buttons (to avoid binding and unbinding buttons)
		self.back_callback		: Callable | None = None
		self.plus_callback		: Callable | None = None
		self.import_callback	: Callable | None = None

		super().__init__(
			MDTopAppBarLeadingButtonContainer(
				self.back_button
			),

			MDTopAppBarTitle(
				text="Simple Password Manager"
			),

			MDTopAppBarTrailingButtonContainer(
				self.import_vault_button,
				self.plus_button,
				self.settings_button
			),

			type="small",
			*args,
			**kwargs
		)

	def on_back(self, instance=None):
		if self.back_callback is not None:
			self.back_callback()

	def on_plus(self, instance=None):
		if self.plus_callback is not None:
			self.plus_callback()

	def on_import(self, instance=None):
		if self.import_callback is not None:
			self.import_callback()