import os
from shutil import copy2, SameFileError

from kivy.utils import platform

from kivymd.uix.filemanager import MDFileManager

from gui.widgets.selection_screen.file_picker import FilePicker, BUFFER_SIZE

from storage.io import VAULT_ENDING

if platform == "android":
	# We require jnius to use Java classes
	from jnius import autoclass, JavaException

	Intent = autoclass("android.content.Intent")						# Create an intent object
	PythonActivity = autoclass("org.kivy.android.PythonActivity")		# Java class hosting this Kivy app
	Activity = autoclass("android.app.Activity")						# Android Activity class; used here for RESULT_* constants
	DocumentsContract = autoclass("android.provider.DocumentsContract")

EXPORT_REQUEST = 1002

class ExportFilePicker(FilePicker):
	ERROR_TITLE = "Export error:"
	def __init__(
		self,
		app_data_path: str,
		vault_name: str,
		*args,
		**kwargs
	):
		super().__init__(
			app_data_path=app_data_path
		)

		self._vault_name = vault_name

		# Only create the MDFileManager instance if we're not on Android
		if platform != "android":
			self._md_file_manager = MDFileManager(
				select_path=lambda dst: self.export_file(
					vault_name=self._vault_name,
					dst=dst
				),
				exit_manager=lambda *args: self.close(),
				search="dirs",
				selector="folder",
				preview=False,
				*args,
				**kwargs
			)

	def export_file(
		self,
		vault_name: str,
		dst: object
	):
		vault_name = os.path.basename(vault_name + VAULT_ENDING)

		src = os.path.join(
			self.app_data_path,
			vault_name
		)

		if not os.path.isfile(src):
			self._emit_error(
				message=f"Vault '{vault_name}' does not exist"
			)
			return

		if platform == "android":
			self._export_android(
				src=src,
				vault_name=vault_name,
				dst=dst
			)
		else:
			self._export_desktop(
				src=src,
				vault_name=vault_name,
				dst=str(dst)
			)

	def _export_desktop(
		self,
		src: str,
		vault_name: str,
		dst: str
	):
		dst_path = os.path.join(
			dst,
			vault_name
		)

		if os.path.exists(dst_path):
			self._emit_error(
				message=f"Vault '{vault_name}' already exists in the selected directory"
			)
			return

		try:
			copy2(
				src=src,
				dst=dst_path
			)
			self.close()
		except SameFileError:
			self._emit_error(
				message="The selected directory is already the application directory"
			)
		except OSError as error:
			self._emit_error(
				message=f"Could not export vault: {error}"
			)

	def _export_android(
		self,
		src: str,
		vault_name: str,
		dst: object
	):
		resolver = PythonActivity.mActivity.getContentResolver()
		output_stream = None

		try:
			# ACTION_OPEN_DOCUMENT_TREE returns a tree URI.
			# createDocument() expects the document URI representing
			# the selected directory.
			directory_uri = DocumentsContract.buildDocumentUriUsingTree(
				dst,
				DocumentsContract.getTreeDocumentId(dst)
			)

			file_uri = DocumentsContract.createDocument(
				resolver,
				directory_uri,
				"application/octet-stream",
				vault_name
			)

			if file_uri is None:
				self._emit_error(
					message="Could not create vault in selected directory"
				)
				return

			output_stream = resolver.openOutputStream(file_uri)

			if output_stream is None:
				self._emit_error(
					message="Could not open output stream to selected directory"
				)
				return

			with open(src, "rb") as input_file:
				buffer = bytearray(BUFFER_SIZE)

				while True:
					count = input_file.readinto(buffer)

					if count == 0:
						break

					output_stream.write(
						buffer,
						0,
						count
					)

		except JavaException as error:
			self._emit_error(
				message=f"Android could not export the vault: {error}"
			)
		except OSError as error:
			self._emit_error(
				message=f"Could not read vault for export: {error}"
			)
		finally:
			if output_stream is not None:
				try:
					output_stream.close()
				except JavaException:
					# The export result is already known. A close failure should not crash the app.
					pass

	def _open_android_picker(self):
		intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)

		self._launch_android_picker(
			intent=intent,
			request_code=EXPORT_REQUEST
		)

	def _on_activity_result(
		self,
		request_code,
		result_code,
		intent
	):
		uri = self._get_activity_result_uri(
			request_code=request_code,
			expected_request_code=EXPORT_REQUEST,
			result_code=result_code,
			intent=intent
		)

		if uri is None:
			return

		self.export_file(
			vault_name=self._vault_name,
			dst=uri
		)
