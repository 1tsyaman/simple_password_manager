from time import time

from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from gui.screens.screen_manager import AppScreenManager

from core.pwd_manager import PwdManager

APP_NAME = "Simple Password Manager"
INACTIVITY_TIMEOUT_DURATION = 60	# seconds

class SimplePasswordManagerApp(MDApp):
	def __init__(self, **kwargs):
		self.watchdog_thread = None
		self.watchdog_deadline = 0

		super().__init__(**kwargs)


	def on_start(self):
		# Reset watchdog on activity
		Window.bind(
			on_touch_down=	lambda *_: self.reset_watchdog(),
			on_key_down=	lambda *_: self.reset_watchdog(),
			on_keyboard=	lambda 	window,
									key,
									scancode,
									codepoint,
									modifiers: self._on_keyboard(key)
		)

		# Start the watchdog timer.
		self.schedule_watchdog()

	def on_pause(self):
		return super().on_pause()

	def on_resume(self):
		if time() >= self.watchdog_deadline:
			# Call the watchdog function
			self.cancel_watchdog_if_scheduled()
			self.lock_vault()

		return super().on_resume()

	def schedule_watchdog(self):
		# Add absolute deadline that can be used if app is paused
		self.watchdog_deadline = time() + INACTIVITY_TIMEOUT_DURATION
		self.watchdog_thread = Clock.schedule_once(
			lambda *_: self.lock_vault(),
			INACTIVITY_TIMEOUT_DURATION,
		)

	def cancel_watchdog_if_scheduled(self):
		if self.watchdog_thread is not None:
			self.watchdog_thread.cancel()

	def reset_watchdog(self):
		self.cancel_watchdog_if_scheduled()
		self.schedule_watchdog()

	def lock_vault(self):
		self.close_all_dialogs()
		self.screen_manager.lock_vault()
		self.schedule_watchdog()

	def close_all_dialogs(self):
		stack = list(Window.children)

		while stack:
			widget = stack.pop()

			if isinstance(widget, MDDialog):
				widget.dismiss()

			stack.extend(widget.children)


	def _on_keyboard(
		self,
		key: int
	) -> bool:
		if key == 27:	# Anroid back button / Esc
			self.screen_manager.current_screen.on_back()
			return True	# Consume this event (interception)

		return False	# Event gets handled by default handler

	def build(self):
		self.app_screen = MDScreen(
			md_bg_color=self.theme_cls.backgroundColor
		)

		# Narrow phone screen in the middle of the app window
		self.phone_screen = MDScreen(
			size_hint_max_x="500dp",
    		pos_hint={
				"center_x": 0.5
			},
			md_bg_color=self.theme_cls.secondaryContainerColor
		)
		# Main container that occupies the whole phone screen
		self.main_container = MDBoxLayout(
			orientation="vertical",
			size_hint=(1,1)
		)

		# Top container (contains TopBar or SearchBar)
		self.top_container = MDBoxLayout(
			size_hint_y=None,
			height="60dp",
		)

		# Occupies the rest of the phone screen
		self.screen_manager = AppScreenManager(
			app=self,
			app_name=APP_NAME,
			phone_screen=self.phone_screen,
			top_container=self.top_container,
			pwd_manager=PwdManager()	# dummy pwd manager to initialize vault screen
		)

		if platform == "android":
			# padding above the top bar
			self.main_container.add_widget(
				MDBoxLayout(
					size_hint_y=None,
					height="30dp"
				)
			)

		self.main_container.add_widget(
			self.top_container
		)
		self.main_container.add_widget(
			self.screen_manager
		)

		self.phone_screen.add_widget(
			self.main_container
		)
		self.app_screen.add_widget(
			self.phone_screen
		)

		return self.app_screen

if __name__ == "__main__":
	SimplePasswordManagerApp().run()