"""
	To communicate incorrect input:
		input = InputField(...)
		...
		input.error_widget.text = "Some error meesage"
		input.error = True
"""
class InputField(MDTextField):
	def __init__(self, *args, title: str, icon: str = "", password=False, **kwargs):
		self.error_widget = MDTextFieldHelperText(text="Initial message", mode="on_error")

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
			*args,
			mode="outlined",
			fill_color_normal="lightcyan",
			fill_color_focus="lightsteelblue",
			theme_line_color="Custom",
			line_color_normal="mediumaquamarine",
			line_color_focus="tan",
			**kwargs
		)

		self.password=password
		self.password_mask="\u2022" # "●"