import os
from threading import Thread
from collections.abc import Callable
from shutil import copy2, SameFileError

from kivy.utils import platform
from kivy.clock import Clock

from kivymd.uix.filemanager import MDFileManager

from gui.dialogs.error_dialog import ErrorDialog

if platform == "android":
	# We require jnius to use Java classes
	from jnius import autoclass, JavaException
	from android import activity	# pyright: ignore[reportMissingImports]

	Intent = autoclass("android.content.Intent")					# Create an intent object
	PythonActivity = autoclass("org.kivy.android.PythonActivity")	# Java class hosting this Kivy app
	OpenableColumns = autoclass("android.provider.OpenableColumns") # For extracting file name from URI
	Activity = autoclass("android.app.Activity")					# Android Activity class; used here for RESULT_* constants

IMPORT_REQUEST = 1001

BUFFER_SIZE = 8192		# 8 KiB

class ImportFilePicker:
	def __init__(
		self,
		app_data_path: str,
		refresh_callback: Callable,
		*args,
		**kwargs
	):
		self.app_data_path = app_data_path
		self.refresh_callback = refresh_callback

		# Only create the MDFileManager instance if we're not on Android
		if platform != "android":
			self._md_file_manager = MDFileManager(
				select_path=self.import_file,
				exit_manager=lambda *args: self.close(),
				ext=[".vault"],
				search="all",
				preview=False,
				*args,
				**kwargs
		)

	def open(self):
		if platform == "android":
			self._open_android_picker()
		else:
			home_dir = os.path.expanduser("~")
			self._md_file_manager.show(home_dir)

	def import_file(
		self,
		src: object
	):
		if platform != "android":
			path = str(src)

			if not path.endswith(".vault"):
				self._emit_error(
					message="Vault files have the extension '.vault'"
				)
				return

			try:
				copy2(
					src=path,
					dst=self.app_data_path
				)
			except SameFileError:
				self._emit_error(
					message="The selected vault is already in the application directory"
				)
				return
			except OSError as e:
				self._emit_error(
					message=f"Could not import vault: {e}"
				)
				return
		else:
			# Get the ContentResolver belonging to the Android Activity hosting this Kivy app
			resolver = PythonActivity.mActivity.getContentResolver()

			try:
				file_name = self._get_filename_from_uri(uri=src)
			except ValueError as e:
				self._emit_error(
					message=str(e)
				)
				return
			except JavaException as e:
				self._emit_error(
					message=f"Android could not read file information: {e}"
				)
				return

			# DISPLAY_NAME should be a file name, but strip path components defensively.
			file_name = os.path.basename(file_name)

			if not file_name.endswith(".vault"):
				self._emit_error(
					message="Vault files have the extension '.vault'"
				)
				return

			input_stream = None

			try:
				input_stream = resolver.openInputStream(src)

				if input_stream is None:
					self._emit_error(
						message="Could not open input stream to selected file"
					)
					return

				dest = os.path.join(self.app_data_path, file_name)

				if os.path.exists(dest):
					self._emit_error(
						message=f"Vault '{file_name}' already exists"
					)
					return

				with open(dest, "wb") as output:
					buffer = bytearray(BUFFER_SIZE)	# 8 KiB

					while True:
						count = input_stream.read(buffer)

						if count == -1:
							break

						output.write(buffer[:count])
			except JavaException as error:
				self._emit_error(
					message=f"Android could not read the selected vault: {error}"
				)
				return
			except OSError as error:
				self._emit_error(
					message=f"Could not write imported vault: {error}"
				)
				return
			finally:
				if input_stream is not None:
					try:
						input_stream.close()
					except JavaException:
						# The import result is already known. A close failure should not crash the app.
						pass

		"""
			on android, this is called from a different thread,
				hence, we need to schedule it on kivy's main thread
		"""
		Clock.schedule_once(
			lambda _: self.refresh_callback()
		)

	def _open_android_picker(self):
		activity.bind(
			# Callback for when the request is fulfilled
			on_activity_result=self._start_on_activity_result_thread
		)

		try:
			intent = Intent(Intent.ACTION_OPEN_DOCUMENT)	# Pre-defined request 'open document'
			intent.addCategory(Intent.CATEGORY_OPENABLE)	# Filter documents to those that can be opened

			"""
				Common MIME types: https://stackoverflow.com/questions/13065838/what-are-the-possible-intent-types-for-intent-settypetype
			"""
			intent.setType("*/*")	# .vault files do not have a standard MIME type, so "*/*" means 'any'

			PythonActivity.mActivity.startActivityForResult(intent, IMPORT_REQUEST)
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

	def _on_activity_result(
		self,
		request_code,
		result_code,
		intent
	):
		if request_code != IMPORT_REQUEST:
			return

		activity.unbind(
			on_activity_result=self._start_on_activity_result_thread
		)

		# RESULT_CANCELED is normal when the user closes the picker without selecting a file.
		if result_code != Activity.RESULT_OK:
			return

		if intent is None:
			self._emit_error(
				message="Android did not return a selected file"
			)
			return

		try:
			uri = intent.getData()	# Android provides a URI instead of a raw path
		except JavaException as error:
			self._emit_error(
				message=f"Could not obtain selected file URI: {error}"
			)
			return

		if uri is None:
			self._emit_error(
				message="Android provided an invalid file URI"
			)
			return

		self.import_file(src=uri)

	def _get_filename_from_uri(self, uri: object) -> str:
		resolver = PythonActivity.mActivity.getContentResolver()

		"""
			Get all available columns of this URI (0-indexed).
			Example result:

			| _display_name      | _size | mime_type                |
			|--------------------|-------|--------------------------|
			| work.vault         | 8120  | application/octet-stream |
		"""
		cursor = resolver.query(
			uri,
			None,	# projection
			None,	# selection
			None,	# selection_args
			None	# sort_order
		)

		try:
			if cursor is not None and cursor.moveToFirst(): # Move to first result row
				index = cursor.getColumnIndex(
					OpenableColumns.DISPLAY_NAME
				)

				if index != -1:
					file_name = cursor.getString(index)

					if file_name is not None:
						return str(file_name)
		finally:
			if cursor is not None:
				cursor.close()

		raise ValueError("Could not determine selected file name")

	def _emit_error(self, message: str):
		"""
			on android, this is called from a different thread,
				hence, we need to schedule it on kivy's main thread
		"""
		Clock.schedule_once(
			lambda _: ErrorDialog(
				error_title="Import error:",
				error_message=message
			).open()
		)
