from collections.abc import Callable

from kivy.uix.widget import Widget
from kivymd.uix.menu import MDDropdownMenu

class VaultContextMenu(MDDropdownMenu):
	def __init__(
		self,
		settings_callback	: Callable,
		export_callback		: Callable,
		rename_callback		: Callable,
		delete_callback		: Callable,
		caller: Widget,
		**kwargs
	):
		self.settings_callback	= settings_callback
		self.export_callback	= export_callback
		self.rename_callback	= rename_callback
		self.delete_callback	= delete_callback

		settings = {
			"text":			"Settings",
			"on_release":	lambda *_: self._settings_callback(),
		}
		export = {
			"text":			"Export",
			"on_release":	lambda *_: self._export_callback(),
		}
		rename = {
			"text":			"Rename",
			"on_release":	lambda *_: self._rename_callback(),
		}
		delete = {
			"text":			"Delete",
			"on_release":	lambda *_: self._delete_callback(),
		}

		super().__init__(
			caller=caller,
			items=[settings, rename, export, delete],
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

	def _settings_callback(self):
		self.dismiss()
		self.settings_callback()

	def _export_callback(self):
		self.dismiss()
		self.export_callback()

	def _rename_callback(self):
		self.dismiss()
		self.rename_callback()

	def _delete_callback(self):
		self.dismiss()
		self.delete_callback()