from kivymd.uix.label import MDLabel

class NoAccountsLabel(MDLabel):
	def __init__(self, *args, **kwargs):
		super().__init__(
			text="Accounts will appear here.",
			halign="center",
			valign="middle",
			*args,
			**kwargs
		)

class NoVaultsLabel(MDLabel):
	def __init__(self, *args, **kwargs):
		super().__init__(
			text="Imported/Created vaults will appear here.",
			halign="center",
			valign="middle",
			*args,
			**kwargs
		)
