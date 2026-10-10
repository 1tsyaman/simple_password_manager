from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from core.sync.backend import RemoteFile, SyncBackend

class GoogleDriveBackend(SyncBackend):

	def __init__(self, credentials):
		# _drive has dynamic type googleapiclient.discovery.Resource
		self._drive = build(
			"drive",
			"v3",
			credentials=credentials,
		)

	def list_files(self) -> list[RemoteFile]:
		response = self._drive.files().list(
						spaces="appDataFolder",
						fields="files(id, name, modifiedTime)",
					).execute()

		return [
			RemoteFile(
				id=file["id"],
				name=file["name"],
				modified_time=file.get("modifiedTime")
			)
				for file in response.get("files", [])
		]

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