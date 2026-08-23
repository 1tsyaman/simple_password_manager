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
		no_callback: Callable,
		yes_callback: Callable,
		icon: str = "",
		*args,
		**kwargs
	):
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
					on_release=lambda _: yes_callback(self)
				),

				MDButton(
					MDButtonText(
						text="No",
					),
					style="text",
					on_release=lambda _: no_callback(self)
				),

				Widget(),
				spacing="8dp",

			),

			*args,
			**kwargs,
		)