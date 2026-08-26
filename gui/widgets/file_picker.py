import os
from threading import Thread

from kivy.utils import platform
from kivy.clock import Clock

from kivymd.uix.filemanager import MDFileManager

from gui.dialogs.error_dialog import ErrorDialog

if platform == "android":
	# We require jnius to use Java classes
	from jnius import autoclass, JavaException
	from android import activity	# pyright: ignore[reportMissingImports]

	Intent = autoclass("android.content.Intent")						# Create an intent object
	PythonActivity = autoclass("org.kivy.android.PythonActivity")		# Java class hosting this Kivy app
	Activity = autoclass("android.app.Activity")						# Android Activity class; used here for RESULT_* constants

BUFFER_SIZE = 8192		# 8 KiB

class FilePicker:
	ERROR_TITLE = "File error:"
	_md_file_manager: MDFileManager | None

	def __init__(
		self,
		app_data_path: str
	):
		self.app_data_path = app_data_path
		self._md_file_manager = None

	def open(self):
		if platform == "android":
			self._open_android_picker()
		else:
			home_dir = os.path.expanduser("~")
			if self._md_file_manager is not None:
				self._md_file_manager.show(home_dir)

	def close(self):
		if platform != "android" and self._md_file_manager is not None:
			self._md_file_manager.close()

	"""
		Should be overridden by Import/ExportFilePicker
	"""
	def _open_android_picker(self):
		raise NotImplementedError

	def _launch_android_picker(
		self,
		intent: object,
		request_code: int
	):
		activity.bind(
			# Callback for when the request is fulfilled
			on_activity_result=self._start_on_activity_result_thread
		)

		try:
			PythonActivity.mActivity.startActivityForResult(
				intent,
				request_code
			)
		except JavaException as error:
			activity.unbind(
				on_activity_result=self._start_on_activity_result_thread
			)
			self._emit_error(
				message=f"Could not open Android file picker: {error}"
			)

	"""
		To avoid the app not resuming because of background copying
			we start the copying on a worker thread and return immediately
	"""
	def _start_on_activity_result_thread(self, *args):
		Thread(
			target=self._on_activity_result,
			args=args,
			daemon=True
		).start()

	"""
		Should be overridden by Import/ExportFilePicker
	"""
	def _on_activity_result(
		self,
		request_code,
		result_code,
		intent
	):
		raise NotImplementedError

	def _get_activity_result_uri(
		self,
		request_code: int,
		expected_request_code: int,
		result_code: int,
		intent: object
	) -> object | None:
		if request_code != expected_request_code:
			return None

		activity.unbind(
			on_activity_result=self._start_on_activity_result_thread
		)

		# RESULT_CANCELED is normal when the user closes the picker without selecting anything.
		if result_code != Activity.RESULT_OK:
			return None

		if intent is None:
			self._emit_error(
				message="Android did not return a selection"
			)
			return None

		try:
			uri = intent.getData()	# Android provides a URI instead of a raw path
		except JavaException as error:
			self._emit_error(
				message=f"Could not obtain selected URI: {error}"
			)
			return None

		if uri is None:
			self._emit_error(
				message="Android provided an invalid URI"
			)
			return None

		return uri

	def _emit_error(self, message: str):
		"""
			on android, this can be called from a different thread,
				hence, we need to schedule it on kivy's main thread
		"""
		Clock.schedule_once(
			lambda _: ErrorDialog(
				error_title=self.ERROR_TITLE,
				error_message=message
			).open()
		)