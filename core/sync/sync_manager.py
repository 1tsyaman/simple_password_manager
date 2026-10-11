from __future__ import annotations
from threading import RLock
from pathlib import Path

from core.sync.backend import SyncBackend

from core.sync.google_drive.backend import GoogleDriveBackend
import core.sync.google_drive.desktop_auth as desktop_auth

from core.etc.errors import (
	ClientCredentialsNotFoundError,
	log
)

"""
	Following needs to be stored (and authenticated) locally:
		{
			"data"	: {
				"vault_id_1" : {
					"remote_file_id"		: str,
					"last_synced_version"	: hex
				},

				"vault_id_2" : ...
				.
				.
				.
			},

			"hmac"	: hex
		}
"""

class SyncManager:
	def __init__(
		self,
		backend		: SyncBackend,
		lock		: RLock		# Guards read/write and remote sync operations on the vault file
	) -> None:
		self.backend	= backend
		self.lock		= lock

	"""
		@raises:
			- ClientCredentialsNotFoundError
			- AuthDeniedError
			- AuthTimeoutError
			- SyncBackendError
	"""
	@staticmethod
	def from_google_drive_token(
		client_credentials_path	: str,
		token_path				: str,
		sync_lock				: RLock
	) -> SyncManager:
		if not Path(client_credentials_path).exists():
			raise ClientCredentialsNotFoundError

		credentials = desktop_auth.get_credentials(
			client_credentials_path=Path(client_credentials_path),
			token_path=Path(token_path)
		)

		backend = GoogleDriveBackend(credentials)

		return SyncManager(
			backend=backend,
			lock=sync_lock
		)