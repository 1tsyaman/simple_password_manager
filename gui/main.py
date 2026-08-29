from threading import Lock
from time import time

from kivy.clock import Clock
from kivy.core.window import Window

from kivymd.uix.boxlayout import MDBoxLayout

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from gui.screens.screen_manager import AppScreenManager

from core.pwd_manager import PwdManager

APP_NAME = "Simple Password Manager"
INACTIVITY_TIMEOUT_DURATION = 60	# seconds

class SimplePasswordManagerApp(MDApp):
	def __init__(self, **kwargs):
		self.modified_lock = Lock()
		self.modified = False	# Shared state which is checked by the watchdog thread
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

	# TODO: Add on_pause behaviour, such as locking the vault
	def on_pause(self):
		return super().on_pause()

	def on_resume(self):
		if time() >= self.watchdog_deadline:
			# Call the watchdog function
			self.kill_if_inactive()

		return super().on_resume()

	def schedule_watchdog(self):
		# Add absolute deadline that can be used if app is paused
		self.watchdog_deadline = time() + INACTIVITY_TIMEOUT_DURATION
		self.watchdog_thread = Clock.schedule_once(
			lambda *_: self.kill_if_inactive(),
			INACTIVITY_TIMEOUT_DURATION,
		)

	def reset_watchdog(self):
		with self.modified_lock:
			self.modified = True

	# TODO: Change this to 'Lock Vault' instead of 'Kill app'
	def kill_if_inactive(self):
		with self.modified_lock:
			if not self.modified:
				self.stop()
			else:
				self.modified = False

		self.schedule_watchdog()

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
			height = "60dp",
		)

		# Occupies the rest of the phone screen
		self.screen_manager = AppScreenManager(
			app=self,
			app_name=APP_NAME,
			phone_screen=self.phone_screen,
			top_container=self.top_container,
			pwd_manager=PwdManager()	# dummy pwd manager to initialize vault screen
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