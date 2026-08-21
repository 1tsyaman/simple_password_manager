class LoginDialog(MDDialog):
	def __init__(self, vault, login_callback, *args, **kwargs):
		self.password_field = InputField(title="Password", icon="lock", password=True)
		self.loading_indicator = MDCircularProgressIndicator(
			size_hint=(None, None),
			pos_hint={"center_x": 0.5},
			size=("32dp", "32dp"), 
			active=False,	# active -> visible
		)

		self.vault = vault
		self.login_callback = login_callback

		super().__init__(
			MDDialogIcon(
				icon="safe",
			),

			MDDialogHeadlineText(
				text=f"Unlock {vault}",
			),

			MDDialogContentContainer(
				self.password_field,
				self.loading_indicator,
				orientation="vertical",
				spacing="10dp",
			),

			MDDialogButtonContainer(
				Widget(),

				MDButton(
					MDButtonText(text="Cancel"),
					style="text",
					on_release=self._dismiss
				),

				MDButton(
					MDButtonText(text="Accept"),
					style="text",
					on_release=self._accept
				),

				spacing="8dp",
			),
			*args,
			**kwargs,
		)

	def _dismiss(self, instance):
		self.dismiss()
		self.password_field.text = ""

	def _accept(self, instance):
		password = self.password_field.text
		self.password_field.text = ""

		self.login_callback(login_dialog=self, vault_name=self.vault, password=password)