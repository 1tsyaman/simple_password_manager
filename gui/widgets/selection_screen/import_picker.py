import os
from collections.abc import Callable
from shutil import copy2, SameFileError

from kivy.utils import platform
from kivy.clock import Clock

from kivymd.uix.filemanager import MDFileManager

from gui.widgets.selection_screen.file_picker import FilePicker, BUFFER_SIZE


if platform == "android":
	# We require jnius to use Java classes
	from jnius import autoclass, JavaException

	Intent = autoclass("android.content.Intent")						# Create an intent object
	PythonActivity = autoclass("org.kivy.android.PythonActivity")		# Java class hosting this Kivy app
	OpenableColumns = autoclass("android.provider.OpenableColumns")		# For extracting file name from URI


IMPORT_REQUEST = 1001

class ImportFilePicker(FilePicker):
	ERROR_TITLE = "Import error:"

	def __init__(
		self,
		app_data_path: str,
		refresh_callback: Callable,
		*args,
		**kwargs
	):
		super().__init__(
			app_data_path=app_data_path
		)

		self.refresh_callback = refresh_callback

		# Only create the MDFileManager instance if we're not on Android
		if platform != "android":
			self._md_file_manager = MDFileManager(
				select_path=self.import_file,
				exit_manager=lambda *args: self.close(),
				ext=[".vault"],
				search="all",
				selector="file",
				preview=False,
				*args,
				**kwargs
			)

	def import_file(
		self,
		src: object
	):
		# Determine the selected file name first so the common checks
		# are the same on desktop and Android.
		if platform != "android":
			file_name = os.path.basename(str(src))
		else:
			try:
				file_name = self._get_filename_from_uri(uri=src)
			except ValueError as error:
				self._emit_error(
					message=str(error)
				)
				return
			except JavaException as error:
				self._emit_error(
					message=f"Android could not read file information: {error}"
				)
				return

			# DISPLAY_NAME should be a file name, but strip path components defensively.
			file_name = os.path.basename(file_name)

		# Shared checks
		if not file_name.endswith(".vault"):
			self._emit_error(
				message="Vault files have the extension '.vault'"
			)
			return

		dst = os.path.join(self.app_data_path, file_name)

		if os.path.exists(dst):
			self._emit_error(
				message=f"Vault '{file_name}' already exists"
			)
			return

		if platform == "android":
			success = self._import_android(
				src=src,
				dst=dst
			)
		else:
			success = self._import_desktop(
				src=str(src),
				dst=dst
			)

		if not success:
			return

		"""
			on android, this is called from a different thread,
				hence, we need to schedule it on kivy's main thread
		"""
		Clock.schedule_once(
			lambda _: self.refresh_callback()
		)

	def _import_desktop(
		self,
		src: str,
		dst: str
	) -> bool:
		try:
			copy2(
				src=src,
				dst=dst
			)
			self.close()
		except SameFileError:
			self._emit_error(
				message="The selected vault is already in the application directory"
			)
			return False
		except OSError as error:
			self._emit_error(
				message=f"Could not import vault: {error}"
			)
			return False

		return True

	def _import_android(
		self,
		src: object,
		dst: str
	) -> bool:
		# Get the ContentResolver belonging to the Android Activity hosting this Kivy app
		resolver = PythonActivity.mActivity.getContentResolver()
		input_stream = None

		try:
			input_stream = resolver.openInputStream(src)

			if input_stream is None:
				self._emit_error(
					message="Could not open input stream to selected file"
				)
				return False

			with open(dst, "wb") as output:
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
			return False
		except OSError as error:
			self._emit_error(
				message=f"Could not write imported vault: {error}"
			)
			return False
		finally:
			if input_stream is not None:
				try:
					input_stream.close()
				except JavaException:
					# The import result is already known. A close failure should not crash the app.
					pass

		return True

	def _open_android_picker(self):
		intent = Intent(Intent.ACTION_OPEN_DOCUMENT)	# Pre-defined request 'open document'
		intent.addCategory(Intent.CATEGORY_OPENABLE)	# Filter documents to those that can be opened

		"""
			Common MIME types: https://stackoverflow.com/questions/13065838/what-are-the-possible-intent-types-for-intent-settypetype
		"""
		intent.setType("*/*")	# .vault files do not have a standard MIME type, so "*/*" means 'any'

		self._launch_android_picker(
			intent=intent,
			request_code=IMPORT_REQUEST
		)

	def _on_activity_result(
		self,
		request_code,
		result_code,
		intent
	):
		uri = self._get_activity_result_uri(
			request_code=request_code,
			expected_request_code=IMPORT_REQUEST,
			result_code=result_code,
			intent=intent
		)

		if uri is None:
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