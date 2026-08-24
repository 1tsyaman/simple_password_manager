from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock

from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField

class AndroidFocusBehaviour:
	def _ensure_visible(
		self,
		dialog: MDDialog,
	):
		# Should only be called from android
		from android import get_keyboard_height  # pyright: ignore[reportMissingImports]
		keyboard_height = get_keyboard_height()

		"""
			transform the coordinates of the bottom-left point of the text field
				into window (relative-) coordinates -> (x, y)
			We only take the y coordinates
			
		"""
		field_bottom = self.to_window(0, 0)[1]
		required_bottom = keyboard_height + dp(12)	# Add 12 dp padding

		if field_bottom >= required_bottom:
			return

		shift = required_bottom - field_bottom

		# Shift dialog up
		current_center_y = dialog.pos_hint.get("center_y", 0.5)

		dialog.pos_hint = {
			"center_x": 0.5,
			"center_y": current_center_y + shift / Window.height
		}

	def _reset_if_unfocused(
			self,
			dialog: MDDialog,
	):
		if self._has_focused_text_field(dialog):
			return

		dialog.pos_hint = {
			"center_x": 0.5,
			"center_y": 0.5
		}

	def _handle_focus(
		self,
		field: MDTextField,
		focused: bool
	):
		if platform != "android":
			return

		dialog = self._get_dialog()

		if dialog is None:
			return

		if focused:
			Clock.schedule_once(
				lambda _: self._ensure_visible(
					dialog=dialog
				),
				0.2,	# time for keyboard to unfold
			)

		else:
			Clock.schedule_once(
				lambda _: self._reset_if_unfocused(
					dialog=dialog
				),
				0.1
			)

	"""
		Assumes the input field is embedded in a dialog
	"""
	def _get_dialog(self) -> MDDialog | None:
		parent = self.parent

		while parent is not None:
			if isinstance(parent, MDDialog):
				return parent

			parent = parent.parent

		return None

	"""
		Recursivly goes down the dialog's children
			and checks if any child text field is in focus
	"""
	def _has_focused_text_field(self, widget) -> bool:
		if isinstance(widget, MDTextField) and widget.focus:
			return True

		return any(
			self._has_focused_text_field(child)
			for child in widget.children
		)

class FocusableTextField(MDTextField, AndroidFocusBehaviour):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.bind(
			focus=self._handle_focus
		)