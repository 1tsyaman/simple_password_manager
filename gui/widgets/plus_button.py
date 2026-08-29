from collections.abc import Callable

from kivymd.uix.button import MDFabButton

class PlusButton(MDFabButton):
	def __init__(
		self,
		callback: Callable,
		**kwargs
	):
		super().__init__(
			icon="plus",
			pos_hint={			# Bottom right corner
				"right": 0.95,
				"y": 0.05,
			},
			on_release=lambda *_: callback(),
			**kwargs
		)
