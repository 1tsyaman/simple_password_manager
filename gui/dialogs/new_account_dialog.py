class NewAccountDialog(MDDialog):
	def __init__(self, add_account_callback, *args, **kwargs):
		self.website_field				= InputField(title="Website")
		self.username_field				= InputField(title="Username")
		self.password_field				= InputField(title="Password", password=True)
		self.description_field			= InputField(title="Description")
		self.add_account_callback		= add_account_callback

		super().__init__(
			MDDialogIcon(
				icon="account",
			),

			MDDialogHeadlineText(
				text=f"Add new account",
			),

			MDDialogContentContainer(
				self.website_field,
				self.username_field,
				self.password_field,
				self.description_field,
				orientation="vertical",
				spacing="30dp"
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(text="Cancel"),
					style="text",
					on_release=self._dismiss
				),

				MDButton(
					MDButtonText(text="Add"),
					style="text",
					on_release=self._add
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _dismiss(self, instance):
		self.dismiss()
		self.website_field.text = ""
		self.username_field.text = ""
		self.password_field.text = ""
		self.description_field.text = ""

	def _add(self, instance):
		website			= self.website_field.text
		username		= self.username_field.text
		password		= self.password_field.text
		description		= self.description_field.text

		self.add_account_callback(dialog=self, website=website, username=username,
							   		password=password, description=description)