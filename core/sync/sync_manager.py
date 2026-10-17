from __future__ import annotations
from dataclasses import dataclass
from threading import RLock
from pathlib import Path
from collections.abc import Callable
from uuid import uuid4, UUID

from core.sync.backend import CloudBackend, RemoteFile, RemoteFolder

from core.sync.google_drive.backend import GoogleDriveBackend
import core.sync.google_drive.desktop_auth as desktop_auth

from core.etc.types import sync_data_t, vault_sync_data_t
from storage.constants import VAULT_ENDING
from core.sync.errors import (
	ClientCredentialsNotFoundError,
	NoVaultSyncDataError,
	CloudBackendError,
	RemoteVaultNotFoundError,
	VaultSyncDataExistsError,
	SyncRollbackError,
	HttpError,
)
from core.etc.errors import IllegalArgumentError

"""
	Following sync_data needs to be stored (and authenticated) locally:
		{
			"data"	: {
				"vault_id_1" : {
					"remote_folder_id"		: str,
					"last_synced_version"	: str
				},

				"vault_id_2" : ...
				.
				.
				.
			},

			"hmac"	: hex
		}
"""

"""
	appData folder should be structured as follows:
		- vault_id_1 (Folder): -> vault files (different versions with timestamps sorted by last_modified)
		- vault_id_2 (Folder): -> ...
		- .
		- .
		- .

	A vault_id folder should contain the following vault files:
		- latest_uuid.vault
		- backup_uuid.vault

		=> where backup vault only replaced with vault files that were just opened successfully
			and latest.vault is updated every sync operation.
"""

@dataclass
class VaultSyncData:
	remote_folder_id	: str
	last_synced_version	: str | None

	def to_dict(self) -> vault_sync_data_t:
		return {
			"remote_folder_id"		: self.remote_folder_id,
			"last_synced_version"	: self.last_synced_version
		}

	@staticmethod
	def from_dict(data: dict[str, str | None]) -> VaultSyncData:
		"""
			Raises:
				IllegalArgumentError: If data is not of the shape
					{
						"remote_folder_id"		: str
						"last_synced_version"	: str | None
					}
		"""
		if not isinstance(data, dict):
			raise IllegalArgumentError

		try:
			remote_folder_id	= data["remote_folder_id"]
			last_synced_version	= data["last_synced_version"]
		except KeyError:
			raise IllegalArgumentError

		if not (
			isinstance(remote_folder_id, str)
			and (
				isinstance(last_synced_version, str) or last_synced_version is None
			)
		):
			raise IllegalArgumentError

		return VaultSyncData(
			remote_folder_id=remote_folder_id,
			last_synced_version=last_synced_version
		)



class SyncManager:
	def __init__(
		self,
		backend					: CloudBackend,
		download_path			: Path,
		sync_data				: dict[str, VaultSyncData],
		sync_data_writeback		: Callable[[sync_data_t], None],
		local_version_getter	: Callable[[str], str],
		lock					: RLock
	) -> None:
		"""
		Args:
			backend: 				Cloud backend used for synchronization.
			download_path: 			Directory for downloading files from the cloud.
			sync_data:				Dictionary containing VaultSyncData.
			sync_data_writeback: 	Callback for writing sync_data to disk.
			local_version_getter:	Callback for getting the local vault version.
			lock:					Guards read/write and sync operations on the vault file.
		"""
		self.backend				= backend
		self.download_path			= download_path
		self.sync_data				= sync_data
		self._sync_data_writeback	= sync_data_writeback
		self.local_version_getter	= local_version_getter
		self.lock					= lock

	def pull_vault(
		self,
		vault_id	: str,
		vault_path	: str
	):
		pass

	def push_vault(
		self,
		vault_id	: str,
		vault_path	: str
	):
		pass

	def sync_vault(
		self,
		vault_id	: str,
		vault_path	: str
	):
		"""
			Compares local and remote vault versions
				- pushes local vault to remote if remote is outdated
				- pulls from remote if local is outdated
		"""
		pass

	def init_vault_sync(
		self,
		vault_id	: str
	) -> None:
		"""
			Creates a remote folder for the vault and initializes the sync vault data
				for the vault's id. Holds self.lock
			Args:
				vault_id:					Id of the vault
			Raises:
				VaultSyncDataExistsError:	If vault_id is already in the sync data
				CloudBackendError:			If the backend fails to create the remote folder
				OSError:					If writing sync_data to disk fails
		"""
		with self.lock:
			if vault_id in self.sync_data.keys():
				raise VaultSyncDataExistsError

			try:
				remote_folder = self.backend.create_folder(vault_id)
			except HttpError:	# TODO: break down this based on http statuses
				raise CloudBackendError

			self.sync_data[vault_id] = VaultSyncData(
				remote_folder_id=remote_folder.remote_id,
				last_synced_version=None
			)

			try:
				self.write_sync_data_to_disk()
			except OSError:
				try:
					self._cleanup_vault_init(
						vault_id=vault_id,
						remote_folder_id=remote_folder.remote_id
					)
				except CloudBackendError as deletion_error:
					raise SyncRollbackError from deletion_error

				raise 

	def delete_remote_vault(
		self,
		vault_id : str
	) -> None:
		"""
			Raises:
				IllegalArgumentError:	If vault_id is not associated with any sync data
				CloudBackendError:		If the backend fails to delete the remote folder
				SyncRollbackError:		If remote folder deletion fails, but rolling back
											on-disk sync data also fails
				OSError:				If writing sync_data to disk fails
		"""
		with self.lock:
			try:
				vault_sync_data = self.sync_data.pop(vault_id)
			except KeyError:
				raise IllegalArgumentError

			try:
				self.write_sync_data_to_disk()
			except OSError:
				self.sync_data[vault_id] = vault_sync_data
				raise

			try:
				remote_folder = RemoteFolder(
					remote_id=vault_sync_data.remote_folder_id,
					name=vault_id
				)
				self.backend.delete_folder_recursive(
					remote_folder
				)
			except HttpError as deletion_error:
				self.sync_data[vault_id] = vault_sync_data

				try:
					self.write_sync_data_to_disk()
				except OSError as rollback_error:
					raise SyncRollbackError from rollback_error

				raise CloudBackendError from deletion_error


	def get_remote_version(
		self,
		vault_id : str
	) -> str:
		"""
			Raises:
				NoVaultSyncDataError:		No VaultSyncData object found for vault_id
				RemoteVaultNotFoundError:	No synced vault file found in cloud
				CloudBackendError:			If the cloud requests do not succeed
		"""
		try:
			folder_id = self.sync_data[vault_id].remote_folder_id
		except KeyError:
			raise NoVaultSyncDataError

		try:
			files = self.backend.list_files(
				RemoteFolder(
					remote_id=folder_id,
					name=vault_id
				)
			)

			latest_vault = self._get_latest_vault_file(files)

			if latest_vault is None:
				raise RemoteVaultNotFoundError

			return _get_version_from_vault_name(latest_vault.name)

		except HttpError:	# TODO: break down this based on http statuses
			raise CloudBackendError

	def get_local_version(
		self,
		vault_id: str
	) -> str:
		return self.local_version_getter(vault_id)

	def write_sync_data_to_disk(self) -> None:
		"""
			Writes self.sync_data to disk. Holds self.lock

			Raises:
				OSError:	Writeback failed
		"""
		with self.lock:
			self._sync_data_writeback(
				self._sync_data_to_dict()
			)

	def get_remote_folder_id(
		self,
		vault_id : str
	) -> str:
		"""
			Raises:
				CloudBackendError:			If the cloud requests do not succeed
				RemoteVaultNotFoundError:	No synced vault folder found in cloud
		"""
		try:
			remote_folder = self.backend.find_folder_by_name(vault_id)

			if remote_folder is None:
				raise RemoteVaultNotFoundError

			return remote_folder.remote_id

		except HttpError:
			raise CloudBackendError

	def _sync_data_to_dict(self) -> sync_data_t:
		return {
			vault_id: self.sync_data[vault_id].to_dict()
							for vault_id in self.sync_data.keys()
		}

	def _cleanup_vault_init(
		self,
		vault_id			: str,
		remote_folder_id	: str
	) -> None:
		"""
			Rolls back changes made when attempting to init vault sync
				- Deletes the remote folder, if created
				- Removes vault data from self.sync_data, if added
			Raises:
				CloudBackendError:	If cloud folder deletion fails
				
		"""
		self.sync_data.pop(vault_id)
		
		try:
			self.backend.delete_folder_recursive(
				RemoteFolder(
					remote_id=remote_folder_id,
					name=vault_id
				)
			)
		except HttpError as deletion_error:
			raise CloudBackendError from deletion_error


	@staticmethod
	def get_fresh_version() -> str:
		return str(uuid4())

	@staticmethod
	def from_google_drive_token(
		client_credentials_path	: str,
		token_path				: str,
		download_path			: str,
		sync_data				: sync_data_t,
		sync_data_writeback		: Callable[[sync_data_t], None],
		local_version_getter	: Callable[[str], str],
		sync_lock				: RLock,
	) -> SyncManager:
		"""
			Args:
				client_credentials_path:		Path for desktop google drive credentials JSON
				token_path:						Path for user access token. This is created
													upon authentication if it doesn't exist
				download_path:					Directory for cloud downloads. This is created
													if it doesn't exist
				sync_data:						Dictionary containg vault ids and their corresponding
													sync data
				sync_data_writeback:			Callback for writing changes of sync_data to disk
				local_version_getter:			Callback for getting the local vault version.
				sync_lock:						The lock that guards read/write and sync operations
													on the vault file.
			Raises:
				ClientCredentialsNotFoundError:	Client credentials path does not exist
				AuthDeniedError:				Authentication Denied
				AuthTimeoutError:				Authentication timedout
				CloudBackendError:				Failed to build Google Drive drive
				IllegalArgumentError:			If sync_data values are not of the shape
													{
														"remote_folder_id"		: str
														"last_synced_version"	: str | None
													}
				OSError:						Failed to create the download directory
		"""
		if not Path(client_credentials_path).exists():
			raise ClientCredentialsNotFoundError

		credentials = desktop_auth.get_credentials(
			client_credentials_path=Path(client_credentials_path),
			token_path=Path(token_path)
		)

		backend = GoogleDriveBackend(credentials)

		path = Path(download_path)

		# Create download directory if not already created
		if not path.is_dir():
			path.mkdir(parents=True, exist_ok=True)

		sync_data_dict = {
			vault_id: VaultSyncData.from_dict(sync_data[vault_id])
				for vault_id in sync_data.keys()
		}

		return SyncManager(
			backend=backend,
			download_path=path,
			sync_data=sync_data_dict,
			sync_data_writeback=sync_data_writeback,
			local_version_getter=local_version_getter,
			lock=sync_lock
		)

	@staticmethod
	def _get_latest_vault_file(files: list[RemoteFile]) -> RemoteFile | None:
		"""
			Returns:
				file: file with name 'latest_uuid.vault' if it exists
				None: Otherwise
		"""
		hits = []
		for file in files:
			if _file_has_valid_latest_format(file.name):
				hits.append(file)

		if len(hits) == 0:
			return None

		hits.sort(
			key=lambda file: file.modified_time,
			reverse=True
		)

		return hits[0]


def _get_version_from_vault_name(name: str) -> str:
	return name.removeprefix("latest_").removesuffix(VAULT_ENDING)


def _is_valid_version(version: str) -> bool:
	try:
		return UUID(version).version == 4
	except ValueError:
		return False


def _file_has_valid_latest_format(name: str) -> bool:
	return (
		name.startswith("latest_")
		and name.endswith(VAULT_ENDING)
		and _is_valid_version(
			_get_version_from_vault_name(name)
		)
	)
