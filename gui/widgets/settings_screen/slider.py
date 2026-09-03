from collections.abc import Callable

from kivy.metrics import dp
from kivy.properties import NumericProperty

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import (
	MDSlider,
	MDSliderHandle,
	MDSliderValueLabel
)

class LargeHitBoxSlider(MDSlider):
	hitbox_padding = NumericProperty(dp(12))

	def __init__(
		self,
		*args,
		**kwargs
	):
		super().__init__(
			MDSliderHandle(),
			MDSliderValueLabel(),
			step=1,
			step_point_size=0,
			size_hint_y=None,
			height=dp(48),
			hitbox_padding=dp(12),
			*args,
			**kwargs
		)

	def collide_point(self, x, y):
		return (
			self.x <= x <= self.right
			and
			self.y - self.hitbox_padding <= y <= self.top + self.hitbox_padding
		)

class SliderSetting(MDBoxLayout):
	def __init__(
		self,
		title				: str,
		value				: int,
		minimum				: int,
		maximum				: int,
		set_value_callback	: Callable,
		*args,
		**kwargs
	):
		super().__init__(
			orientation="vertical",
			adaptive_height=True,
			spacing=dp(4),
			padding=(dp(8), dp(8), dp(8), dp(12)),
			*args,
			**kwargs
		)

		self.set_value_callback = set_value_callback

		self.label = MDLabel(
			text=f"{title}: {value}",
			adaptive_height=True
		)

		self.add_widget(
			self.label
		)

		slider = LargeHitBoxSlider(
			min=minimum,
			max=maximum,
			value=value,
		)

		slider.bind(
			value=lambda _, new_value: self._on_value(title, new_value)
		)

		self.add_widget(slider)

	def _on_value(
		self,
		title		: str,
		new_value	: int
	):
		new_value = int(new_value)
		self.label.text = f"{title}: {new_value}"
		self.set_value_callback(new_value)