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
		headline		: str,
		message			: str,
		yes_callback	: Callable,
		no_callback		: Callable | None = None,	# if None, this is simply 'dismiss'
		yes_text		: str = "Yes",
		no_text			: str = "No",
		red_option		: str = "yes",	# which button is red ['yes', 'no']
		icon			: str = "",
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

		yes_button = MDButtonText(
			text=yes_text,
		)
		no_button = MDButtonText(
			text=no_text,
		)

		if red_option.lower() == 'yes':
			yes_button.theme_text_color = "Custom"
			yes_button.text_color=app.theme_cls.errorColor
		elif red_option.lower() == "no":
			no_button.theme_text_color = "Custom"
			no_button.text_color=app.theme_cls.errorColor


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
					yes_button,
					style="text",
					on_release=lambda _: self._yes_callback()
				),

				MDButton(
					no_button,
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