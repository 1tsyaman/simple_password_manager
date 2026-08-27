from collections.abc import Callable

from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty

from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField, MDTextFieldTrailingIcon

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
	trailing_icon = StringProperty("")

	def __init__(
		self,
		*args,
		trailing_icon: str = "",
		trailing_callback: Callable | None = None,
		**kwargs
	):
		self.trailing_callback	= trailing_callback

		self._trailing_icon_widget = MDTextFieldTrailingIcon(
			icon=trailing_icon
		)

		super().__init__(
			self._trailing_icon_widget,
			*args,
			**kwargs
		)

		self.bind(
			focus=self._handle_focus,
			trailing_icon=self._switch_icon
		)

	def _switch_icon(
			self,
			instance,
			value: str
		):
		self._trailing_icon_widget.icon = value

	def toggle_password_mask(self):
		self.password = not self.password

	def password_mask_is_set(self):
		return self.password

	"""
		Workaround to make the icon behave like a clickable button
	"""
	def on_touch_down(self, touch):
		if self.trailing_callback is not None:
			"""
				The icon is not an actual widget, rather is a shape drawn by KivyMd.
				We get the coordinates it occupies from KivyMd
					bottom-left = (icon_x, icon_y)
					+------------------+
					|                  |
					|       icon       |  icon_h
					|                  |
					+------------------+
							icon_w
			"""
			icon_x, icon_y = self.get_adjusted_pos_trailing_icon()
			icon_w, icon_h = self._trailing_icon_widget.texture_size

			# Makeshift trailing_point.collide_point() check
			if (
				icon_x <= touch.x <= icon_x + icon_w
				and icon_y <= touch.y <= icon_y + icon_h
			):
				self.trailing_callback()
				return True

		return super().on_touch_down(touch)