from collections.abc import Callable

from kivy.uix.widget import Widget
from kivymd.uix.menu import MDDropdownMenu

class VaultContextMenu(MDDropdownMenu):
	def __init__(
		self,
		export_callback: Callable,
		rename_callback: Callable,
		caller: Widget,
		**kwargs
	):
		self.export_callback = export_callback
		self.rename_callback = rename_callback

		export = {
			"text":			"Export",
			"on_release":	lambda *args: self._export_callback(),
		}
		rename = {
			"text":			"Rename",
			"on_release":	lambda *args: self._rename_callback(),
		}

		super().__init__(
			caller=caller,
			items=[rename, export],
			hor_growth="left",		# horizontal growth in relation to the caller
			ver_growth="down",		# vertical grwoth in relation to the caller
			**kwargs
		)

	"""
		Make the menu originate from the button, instead from the corner somewhere
	"""
	def on_open(self, *args):
		self.scale_value_center = self._start_coords
		super().on_open(*args)

	def _export_callback(self):
		self.dismiss()
		self.export_callback()

	def _rename_callback(self):
		self.dismiss()
		self.rename_callback()