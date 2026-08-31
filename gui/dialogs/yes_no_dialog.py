from collections.abc import Callable

from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import (
	MDDialog,
	MDDialogHeadlineText,
	MDDialogSupportingText,
	MDDialogIcon,
	MDDialogButtonContainer
)

class YesNoDialog(MDDialog):
	def __init__(
		self,
		headline: str,
		message: str,
		yes_callback: Callable,
		no_callback: Callable | None = None,	# if None, this is simply 'dismiss'
		icon: str = "",
		*args,
		**kwargs
	):
		self.yes_callback	= yes_callback
		self.no_callback	= no_callback

		icon_widget = []

		if icon != "":
			icon_widget.append(
				MDDialogIcon(
					icon=icon
				)
			)

		app = MDApp.get_running_app()
		assert app is not None

		super().__init__(
			*icon_widget,	# no widget if no icon is provided

			MDDialogHeadlineText(
				text=headline,
			),

			MDDialogSupportingText(
				text=message
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(
						text="Yes",
						theme_text_color="Custom",
		    			text_color=app.theme_cls.errorColor,
					),
					style="text",
					on_release=lambda _: self._yes_callback()
				),

				MDButton(
					MDButtonText(
						text="No",
					),
					style="text",
					on_release=lambda _: self._no_callback()
				),

				Widget(),
				spacing="8dp",

			),

			*args,
			**kwargs,
		)

	def _yes_callback(self):
		self.dismiss()
		self.yes_callback()

	def _no_callback(self):
		self.dismiss()

		if self.no_callback is not None:
			self.no_callback