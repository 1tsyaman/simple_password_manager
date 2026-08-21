from collections.abc import Callable
from kivy.lang.builder import Builder
from kivymd.uix.appbar import MDTopAppBar

class TopBar(MDTopAppBar):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.back_callback : Callable | None = None			# indirect on_release callback for the back button
		self.plus_callback : Callable | None = None

	# direct on_release callback for the back button
	def on_back(self, instance=None):
		print("clicked!")
		if self.back_callback is not None:
			self.back_callback()

	def on_plus(self, instance=None):
		if self.plus_callback is not None:
			self.plus_callback()

Builder.load_file("top_bar.kv")