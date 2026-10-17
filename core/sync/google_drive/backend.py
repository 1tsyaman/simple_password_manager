from pathlib import Path
from datetime import datetime

from googleapiclient.discovery import build, MutualTLSChannelError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import googleapiclient.errors as googleErrors

import storage.io as io
from core.sync.backend import RemoteFile, RemoteFolder, CloudBackend
from core.sync.errors import (
	CloudBackendError,
	HttpError,
)
from core.etc.errors import (
	IllegalArgumentError,
)
class GoogleDriveBackend(CloudBackend):
	APPDATA				= "appDataFolder"
	FILE_FIELDS			= "id, name, modifiedTime"
	FOLDER_MIME_TYPE	= "application/vnd.google-apps.folder"

	def __init__(self, credentials):
		"""
			Raises:
				- CloudBackendError
		"""
		# _drive has dynamic type googleapiclient.discovery.Resource
		try:
			self._drive = build(
				"drive",
				"v3",
				credentials=credentials,
			)
		except MutualTLSChannelError:
			raise CloudBackendError

	def list_files(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFile]:
		files = self._list_files(
			folders=False,
			parent=parent
		)

		return [
			RemoteFile(
				remote_id=file["id"],
				name=file["name"],
				modified_time=self._format_time(file["modifiedTime"])
			)
				for file in files
		]

	def list_folders(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFolder]:
		folders = self._list_files(
			folders=True,
			parent=parent
		)

		return [
			RemoteFolder(
				remote_id=folder["id"],
				name=folder["name"],
			)
				for folder in folders
		]

	def find_file_by_name(
		self,
		name		: str,
		parent		: RemoteFolder | None = None
	) -> RemoteFile | None:
		file = self._find_file_by_name(
			name=name,
			is_folder=False,
			parent=parent
		)
		assert not isinstance(file, RemoteFolder)
	
		return file

	def find_folder_by_name(
		self,
		name		: str,
		parent		: RemoteFolder | None = None
	) -> RemoteFolder | None:
		folder = self._find_file_by_name(
			name=name,
			is_folder=True,
			parent=parent
		)
		assert not isinstance(folder, RemoteFile)
	
		return folder

	"""
		Documentation for:
			- files().create: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create
	"""
	def create_folder(
		self,
		name	: str,
		parent	: RemoteFolder | None = None
	) -> RemoteFolder:
		parents = [parent.remote_id] if parent is not None else [self.APPDATA]

		try:
			folder_metadata = {
				"name"		: name,
				"mimeType"	: self.FOLDER_MIME_TYPE,
				"parents"	: parents
			}

			folder = self._drive.files().create(
				body=folder_metadata,
				fields=self.FILE_FIELDS
			).execute()

			return RemoteFolder(
				remote_id=folder["id"],
				name=folder["name"],
			)
		except googleErrors.HttpError as e:
			raise HttpError(e)

	def upload_file(
		self,
		remote_name	: str,
		source		: Path,
		parent		: RemoteFolder | None = None
	) -> RemoteFile:
		parents = [parent.remote_id] if parent is not None else [self.APPDATA]

		try:
			file_metadata = {
				"name"		: remote_name,
				"parents"	: parents,
			}

			media = MediaFileUpload(
				source,
				resumable=False
			)

			file = self._drive.files().create(
				body=file_metadata,
				media_body=media,
				fields=self.FILE_FIELDS
			).execute()

			return RemoteFile(
				remote_id=file["id"],
				name=file["name"],
				modified_time=self._format_time(file["modifiedTime"])
			)

		except googleErrors.HttpError as e:
			raise HttpError(e)


	def download_file(
		self,
		file		: RemoteFile,
		destination	: Path,
		parent		: RemoteFolder | None = None	# Not required for google-drive
	) -> None:
		try:
			request = self._drive.files().get_media(
				fileId=file.remote_id
			)

			with destination.open("wb") as fd:
				downloader = MediaIoBaseDownload(
					fd=fd,
					request=request
				)

				done = False

				while done is False:
					status, done = downloader.next_chunk()

		except googleErrors.HttpError as e:
			raise HttpError(e)

	def download_folder(
		self,
		folder		: RemoteFolder,
		destination	: Path,
		parent		: RemoteFolder | None = None
	) -> None:
		stack : list[tuple[RemoteFile | RemoteFolder, Path]] = [
			(folder, destination)
		]

		while stack:
			curr, dest = stack.pop()

			if not isinstance(curr, RemoteFolder):
				self.download_file(
					file=curr,
					destination=dest
				)

				continue

			dest = dest.joinpath(curr.name)
			dest.mkdir(parents=True, exist_ok=True)

			stack.extend(
				[
					(file, dest) 
						for file in self.list_files(parent=curr) + self.list_folders(parent=curr)
				]
			)

	def update_file(
		self,
		file	: RemoteFile,
		source	: Path | None = None,
		name	: str | None = None,
		parent	: RemoteFolder | None = None	# Not required for google-drive
	) -> RemoteFile:
		if source is None and name is None:
			raise IllegalArgumentError

		kwargs = {}

		if name is not None:
			kwargs["body"] = {
				"name": name
			}

		if source is not None:
			kwargs["media_body"] = MediaFileUpload(
				source,
				resumable=False
			)

		try:
			response = self._drive.files().update(
				fileId=file.remote_id,
				fields=self.FILE_FIELDS,
				**kwargs
			).execute()

			return RemoteFile(
				remote_id=response["id"],
				name=response["name"],
				modified_time=self._format_time(response["modifiedTime"])
			)

		except googleErrors.HttpError as e:
			raise HttpError(e)


	def delete_file(
		self,
		file	: RemoteFile,
		parent	: RemoteFolder | None = None	# Not required for google-drive
	) -> None:
		self._delete_file(file)

	def delete_folder_recursive(
		self,
		folder	: RemoteFolder,
		parent	: RemoteFolder | None = None	# Not required for google-drive
	) -> None:
		self._delete_file(folder)

	def wipe_appData(self) -> None:
		ls = self.list_files() + self.list_folders()

		for file in ls:
			self._delete_file(file)


	"""
		Documentation for
			- files().list: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list
			- Queries: https://developers.google.com/workspace/drive/api/guides/ref-search-terms
			- Mime Types: https://developers.google.com/workspace/drive/api/guides/mime-types
	"""
	def _list_files(
		self,
		folders	: bool, 
		parent	: RemoteFolder | None = None,
	) -> list[dict[str, str]]:
		"""
			If folders is True, this method returns the list of *folders*,
				otherwise, the list of *files*

			Returns:
				List of file dictionaries of the type:
					{
						"id"			: str,
						"name"			: str,
						"modifiedTime"	: str
					}
		"""
		if parent is None:
			query = "'appDataFolder' in parents"
		else:
			query = f"'{parent.remote_id}' in parents"

		operator = "=" if folders else "!="

		query += f" and mimeType {operator} '{self.FOLDER_MIME_TYPE}'"
		query += " and trashed = false"

		ls : list[dict[str, str]] = []
		next_page_token = None

		try:
			while True:
				response = self._drive.files().list(
								spaces=self.APPDATA,
								q=query,
								fields=f"nextPageToken,files({self.FILE_FIELDS})",
								orderBy="name_natural",
								pageToken=next_page_token
							).execute()

				ls.extend(response.get("files", []))

				next_page_token = response.get("nextPageToken")

				if next_page_token is None:
					break

		except googleErrors.HttpError as e:
			raise HttpError(e)

		return ls

	def _find_file_by_name(
		self,
		name		: str,
		is_folder	: bool,
		parent		: RemoteFolder | None = None
	) -> RemoteFile | RemoteFolder | None:
		"""
			is_folder flag determines if the target file is a folder.
		"""
		files = self.list_folders(parent) if is_folder \
			else self.list_files(parent)

		for file in files:
			if file.name.strip().lower() == name.strip().lower():
				return file

		return None

	def _delete_file(
		self,
		file : RemoteFile | RemoteFolder
	) -> None:
		try:
			self._drive.files().delete(
				fileId=file.remote_id
			).execute()
		except googleErrors.HttpError as e:
			raise HttpError(e)

	@staticmethod
	def _format_time(time: str) -> datetime:
		return datetime.fromisoformat(
			time.removesuffix("Z") + "+00:00"
		)
