from collections.abc import Callable

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout	# for bypassing the ButtonBehavior touch handlers

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDButtonText

class DecorativeCard(MDCard):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.orientation		= "vertical"
		self.style				= "elevated"
		self.spacing			= "8dp"
		self.padding			= "24dp"
		self.size_hint			= (None, None)
		self.allow_hover		= False
		self.ripple_behavior	= False

	# Propagate the touches to the BoxLayout layer underneath the ButtonBehavior layer
	def on_touch_down(self, touch):
		return BoxLayout.on_touch_down(self, touch)

	def on_touch_up(self, touch):
		return BoxLayout.on_touch_up(self, touch)


class NoVaultWidget(DecorativeCard):
	def __init__(
		self,
		create_callback: Callable,
		import_callback: Callable,
		**kwargs
	):
		super().__init__(
			width="320dp",
			height="190dp",
			**kwargs
		)

		app = MDApp.get_running_app()
		assert app is not None

		self.md_bg_color = app.theme_cls.secondaryContainerColor

		self.add_widget(
			MDLabel(
				text="Set up your vault",
				halign="center",
				adaptive_height=True,
				theme_text_color="Primary",
				font_style="Title",
				role="medium",
			)
		)

		self.add_widget(
			Widget(
				size_hint_y=None,
				height="16dp"
			)
		)

		self.add_widget(
			MDButton(
				MDButtonText(text="Create Vault"),
				style="filled",
				pos_hint={"center_x": 0.5},
				on_release=lambda *_: create_callback()
			)
		)

		self.add_widget(
			MDButton(
				MDButtonText(text="Import Vault"),
				style="text",
				pos_hint={"center_x": 0.5},
				on_release=lambda *_: import_callback()
			)
		)

class OpenVaultWidget(DecorativeCard):
	def __init__(
		self,
		open_callback: Callable,
		**kwargs
	):
		super().__init__(
			width="320dp",
			height="150dp",
			**kwargs
		)

		app = MDApp.get_running_app()
		assert app is not None

		self.md_bg_color = app.theme_cls.secondaryContainerColor

		self.add_widget(
			MDLabel(
				text="Welcome Back!",
				halign="center",
				adaptive_height=True,
				theme_text_color="Primary",
				font_style="Title",
				role="medium",
			)
		)

		self.add_widget(
			Widget(
				size_hint_y=None,
				height="10dp"
			)
		)

		self.add_widget(
			MDButton(
				MDButtonText(text="Open Vault"),
				style="filled",
				pos_hint={"center_x": 0.5},
				on_release=lambda *_: open_callback()
			)
		)