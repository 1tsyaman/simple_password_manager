from collections.abc import Callable

from kivymd.uix.textfield import (
	MDTextFieldHelperText,
	MDTextFieldHintText,
	MDTextFieldLeadingIcon,
)

from gui.widgets.focusable_text_field import FocusableTextField
from gui.constants import PASSWORD_MASK

"""
	To communicate incorrect input:
		input = InputField(...)
		...
		input.error_widget.text = "Some error meesage"
		input.error = True
"""
class InputField(FocusableTextField):
	def __init__(
		self,
		*args,
		title: str,
		icon: str = "",
		password: bool = False,	# defines if text is masked or not
		trailing_icon: str = "",
		trailing_callback: Callable | None = None,
		**kwargs
	):
		self.error_widget = MDTextFieldHelperText(
			text="Initial message",
			mode="on_error"
		)

		super().__init__(
			MDTextFieldLeadingIcon(
				icon=icon,
				theme_icon_color="Custom",
				icon_color_normal="mediumaquamarine",
				icon_color_focus="tan",
			),

			self.error_widget,

			MDTextFieldHintText(
				text=title,
				text_color_normal="mediumaquamarine",
				text_color_focus="tan",
			),

			trailing_icon=trailing_icon,
			trailing_callback=trailing_callback,

			mode="outlined",
			fill_color_normal="lightcyan",
			fill_color_focus="lightsteelblue",
			theme_line_color="Custom",
			line_color_normal="mediumaquamarine",
			line_color_focus="tan",
			password=password,
			password_mask=PASSWORD_MASK,

			*args,
			**kwargs
		)

class PasswordInputField(InputField):
    def __init__(
        self,
        *args,
        title: str,
        icon: str = "lock",
        **kwargs
    ):
        super().__init__(
            *args,
            title=title,
            icon=icon,
            password=True,
            trailing_icon="eye",
            trailing_callback=self.toggle_password_mask,
            **kwargs
        )