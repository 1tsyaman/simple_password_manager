from pathlib import Path

from googleapiclient.discovery import build, MutualTLSChannelError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from core.sync.backend import RemoteFile, RemoteFolder, SyncBackend
from core.sync.errors import (
	SyncBackendError
)
class GoogleDriveBackend(SyncBackend):
	APPDATA = "appDataFolder"
	FILE_FIELDS = "id, name, modifiedTime"

	"""
		@raises:
			- SyncBackendError
	"""
	def __init__(self, credentials):
		# _drive has dynamic type googleapiclient.discovery.Resource
		try:
			self._drive = build(
				"drive",
				"v3",
				credentials=credentials,
			)
		except MutualTLSChannelError:
			raise SyncBackendError

	"""
		Documentation for
			- files().list: https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list
			- Queries: https://developers.google.com/workspace/drive/api/guides/ref-search-terms
			- Mime Types: https://developers.google.com/workspace/drive/api/guides/mime-types
	"""
	def list_files(
		self,
		parent: RemoteFolder | None = None
	) -> list[RemoteFile]:
		if parent is None:
			query = "'appDataFolder' in parents"
		else:
			query = f"'{parent.remote_id}' in parents"

		query += " and mimeType != 'application/vnd.google-apps.folder'"
		query += " and trashed = false"

		next_page_token = None
		files = []

		while True:
			response = self._drive.files().list(
							spaces=self.APPDATA,
							q=query,
							fields=f"nextPageToken,files({self.FILE_FIELDS})",
							orderBy="name_natural",
							pageToken=next_page_token
						).execute()

			files.extend(
					RemoteFile(
						remote_id=file["id"],
						name=file["name"],
						modified_time=file.get("modifiedTime")
					)
						for file in response.get("files", [])
			)

			next_page_token = response.get("nextPageToken")

			if next_page_token is None:
				break

		return files

	def find_file(
		self,
		name: str,
	) -> RemoteFile | None:
		files = self.list_files()

		matches = [file for file in files
		           		if file.name == name]

		if len(matches) > 1:
			raise RuntimeError(f"Multiple remote files named {name}")

		if not matches:
			return None

		return matches[0]

	def upload_file(
		self,
	    path: Path
	) -> RemoteFile:
		metadata = {
			"name": path.name,
			"parents": ["appDataFolder"],
		}

		media = MediaFileUpload(
			path,
			resumable=False,
		)

		"""
			result value example:
				{
					'id'			: '1pxCNSXMu7c1azAaV7BrNkmA-c_1NnDagccanVuYngVPM05V7I9w',
					'name'			: 'drive_api.py',
					'modifiedTime'	: '2026-09-26T09:28:39.430Z'
				}
		"""
		result = self._drive.files().create(
			body=metadata,
			media_body=media,
			fields="id, name, modifiedTime",
		).execute()

		return RemoteFile(
			id=result["id"],
			name=result["name"],
			modified_time=result.get("modifiedTime")
		)

	def download_file(
		self,
		file_id		: str,
		destination	: Path,
	) -> None:
		request = self._drive.files().get_media(
			fileId=file_id
		)

		with destination.open("wb") as file:
			downloader = MediaIoBaseDownload(
				file,
				request,
			)

			done = False

			while not done:
				_, done = downloader.next_chunk()

	def update_file(
		self,
		file_id	: str,
		path	: Path,
	) -> RemoteFile:
		media = MediaFileUpload(
			path,
			resumable=False,
		)

		result = self._drive.files().update(
			fileId=file_id,
			media_body=media,
			fields="id, name, modifiedTime",
		).execute()

		return RemoteFile(
			id=result["id"],
			name=result["name"],
			modified_time=result.get("modifiedTime")
		)