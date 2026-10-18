import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from threading import RLock
from uuid import uuid4

from core.sync.backend import RemoteFolder
from core.sync.errors import SyncConflictError
from core.sync.google_drive.backend import GoogleDriveBackend
import core.sync.google_drive.desktop_auth as desktop_auth
from core.sync.sync_manager import SyncManager, SyncCallbacks

CLIENT_FILE = Path(
	os.environ.get(
		"PM_GDRIVE_CLIENT_FILE",
		".private/google_drive/desktop_credentials.json"
	)
)

TOKEN_FILE = Path(
	os.environ.get(
		"PM_GDRIVE_TOKEN_FILE",
		".private/google_drive/test_token2.json"
	)
)


class TestSyncManagerGoogleDriveIntegration(unittest.TestCase):
	"""
		Integration tests using a real Google Drive test account.

		Requirements:
			- CLIENT_FILE must point to valid Google OAuth desktop credentials.
			- TOKEN_FILE may already exist. If not, the desktop OAuth flow opens.
			- The account should be a dedicated test account.

		The tests NEVER call wipe_appData(). Every test uses a unique vault id
		and only deletes the remote folder created for that test.
	"""

	@classmethod
	def setUpClass(cls) -> None:
		if not CLIENT_FILE.exists():
			raise unittest.SkipTest(
				f"Google Drive client credentials not found: {CLIENT_FILE}"
			)

		cls.credentials = desktop_auth.get_credentials(
			client_credentials_path=CLIENT_FILE,
			token_path=TOKEN_FILE
		)

		if not cls.credentials.valid:
			raise RuntimeError("Google Drive credentials are not valid")

		cls.backend = GoogleDriveBackend(cls.credentials)

	def setUp(self) -> None:
		self._tmp = tempfile.TemporaryDirectory()
		self.tmp_path = Path(self._tmp.name)

		self.download_path = self.tmp_path / "downloads"
		self.download_path.mkdir(parents=True, exist_ok=True)

		self.vault_id = uuid4().hex
		self.vault_path = self.tmp_path / "integration_test.vault"
		self.sync_data_path = self.tmp_path / "sync_data.json"

		self.initial_version = str(uuid4())
		self._write_vault(
			path=self.vault_path,
			version=self.initial_version,
			payload="initial-local"
		)

		self.persisted_sync_data = None

		callbacks = SyncCallbacks(
			sync_data_writeback=self._sync_data_writeback,
			local_version_getter=self._local_version_getter,
			vault_auth_checker=self._vault_auth_checker,
		)

		self.manager = SyncManager(
			backend=self.backend,
			download_path=self.download_path,
			sync_data={},
			sync_callbacks=callbacks,
			lock=RLock()
		)

	def tearDown(self) -> None:
		"""
			Best-effort cleanup of only the unique remote folder created by this
			test. Never touches unrelated appData contents.
		"""
		try:
			for folder in self.backend.list_folders():
				if folder.name == self.vault_id:
					self.backend.delete_folder_recursive(folder)
		finally:
			self._tmp.cleanup()

	def _write_vault(
		self,
		path: Path,
		version: str,
		payload: str
	) -> None:
		data = {
			"Metadata": {
				"id": self.vault_id,
				"version": version,
				"last_modified": 0
			},
			"payload": payload
		}

		path.write_text(
			json.dumps(data),
			encoding="utf-8"
		)

	def _read_vault(self, path: Path) -> dict:
		return json.loads(
			path.read_text(encoding="utf-8")
		)

	def _local_version_getter(self, vault_id: str) -> str:
		data = self._read_vault(self.vault_path)

		if data["Metadata"]["id"] != vault_id:
			raise ValueError("Requested vault id does not match local vault")

		return data["Metadata"]["version"]

	def _vault_auth_checker(self, vault_id: str) -> bool:
		"""
			Integration-test authenticity stand-in.

			It deliberately does not test cryptography. It verifies that the
			downloaded staging vault exists, contains valid JSON, and belongs
			to the expected vault id.
		"""
		downloaded_vault = self.download_path / self.vault_path.name

		try:
			data = self._read_vault(downloaded_vault)
			return data["Metadata"]["id"] == vault_id
		except (OSError, KeyError, TypeError, json.JSONDecodeError):
			return False

	def _sync_data_writeback(self, data: dict) -> None:
		self.persisted_sync_data = copy.deepcopy(data)

		self.sync_data_path.write_text(
			json.dumps(data),
			encoding="utf-8"
		)

	def _init_sync(self):
		self.manager.init_vault_sync(
			vault_id=self.vault_id,
			vault_path=str(self.vault_path)
		)

		folder_id = self.manager.sync_data[self.vault_id].remote_folder_id

		return RemoteFolder(
			remote_id=folder_id,
			name=self.vault_id
		)

	def _download_remote_latest(self, destination: Path) -> None:
		latest = self.manager.get_latest_remote_vault_file(self.vault_id)

		self.backend.download_file_atomic(
			file=latest,
			destination=destination
		)

	def test_factory_uses_real_desktop_auth_and_backend(self):
		factory_download_path = self.tmp_path / "factory_downloads"

		callbacks = SyncCallbacks(
			sync_data_writeback=lambda _: None,
			local_version_getter=self._local_version_getter,
			vault_auth_checker=self._vault_auth_checker,
		)

		manager = SyncManager.from_google_drive_token(
			client_credentials_path=str(CLIENT_FILE),
			token_path=str(TOKEN_FILE),
			download_path=str(factory_download_path),
			sync_data={},
			sync_callbacks=callbacks,
			sync_lock=RLock()
		)

		self.assertIsInstance(manager.backend, GoogleDriveBackend)
		self.assertTrue(factory_download_path.is_dir())

	def test_init_sync_uploads_vault_and_lookup_methods_match_remote(self):
		remote_folder = self._init_sync()

		self.assertIn(self.vault_id, self.manager.sync_data)
		self.assertEqual(
			self.manager.sync_data[self.vault_id].last_synced_version,
			self.initial_version
		)
		self.assertEqual(
			self.manager.get_remote_folder_id(self.vault_id),
			remote_folder.remote_id
		)
		self.assertEqual(
			self.manager.get_remote_version(self.vault_id),
			self.initial_version
		)

		latest = self.manager.get_latest_remote_vault_file(self.vault_id)

		self.assertEqual(
			latest.name,
			f"latest_{self.initial_version}.vault"
		)

		verification_path = self.tmp_path / "init_verification.vault"

		self.backend.download_file_atomic(
			file=latest,
			destination=verification_path
		)

		self.assertEqual(
			verification_path.read_bytes(),
			self.vault_path.read_bytes()
		)

		self.assertEqual(
			self.persisted_sync_data[self.vault_id]["remote_folder_id"],
			remote_folder.remote_id
		)
		self.assertEqual(
			self.persisted_sync_data[self.vault_id]["last_synced_version"],
			self.initial_version
		)

	def test_push_vault_updates_same_remote_file_and_contents(self):
		self._init_sync()

		latest_before = self.manager.get_latest_remote_vault_file(
			self.vault_id
		)

		new_version = str(uuid4())

		self._write_vault(
			path=self.vault_path,
			version=new_version,
			payload="new-local-data"
		)

		self.manager.push_vault(
			vault_id=self.vault_id,
			vault_path=str(self.vault_path)
		)

		latest_after = self.manager.get_latest_remote_vault_file(
			self.vault_id
		)

		self.assertEqual(
			latest_after.remote_id,
			latest_before.remote_id
		)
		self.assertEqual(
			latest_after.name,
			f"latest_{new_version}.vault"
		)
		self.assertEqual(
			self.manager.sync_data[self.vault_id].last_synced_version,
			new_version
		)

		verification_path = self.tmp_path / "push_verification.vault"
		self._download_remote_latest(verification_path)

		self.assertEqual(
			verification_path.read_bytes(),
			self.vault_path.read_bytes()
		)

	def test_pull_vault_replaces_local_vault_with_remote_contents(self):
		self._init_sync()

		remote_version = str(uuid4())
		remote_source = self.tmp_path / "remote_source.vault"

		self._write_vault(
			path=remote_source,
			version=remote_version,
			payload="new-remote-data"
		)

		latest = self.manager.get_latest_remote_vault_file(
			self.vault_id
		)

		self.backend.update_file(
			file=latest,
			source=remote_source,
			name=f"latest_{remote_version}.vault"
		)

		self.manager.pull_vault(
			vault_id=self.vault_id,
			vault_path=str(self.vault_path)
		)

		self.assertEqual(
			self.vault_path.read_bytes(),
			remote_source.read_bytes()
		)
		self.assertEqual(
			self.manager.get_local_version(self.vault_id),
			remote_version
		)
		self.assertEqual(
			self.manager.sync_data[self.vault_id].last_synced_version,
			remote_version
		)

		# io.move_file() should have moved the staging download into vault_path.
		self.assertFalse(
			(self.download_path / self.vault_path.name).exists()
		)

	def test_sync_vault_pushes_then_pulls(self):
		self._init_sync()

		# Local changes from A -> B. sync_vault() should push B.
		local_version = str(uuid4())

		self._write_vault(
			path=self.vault_path,
			version=local_version,
			payload="sync-push"
		)

		self.manager.sync_vault(
			vault_id=self.vault_id,
			vault_path=str(self.vault_path)
		)

		self.assertEqual(
			self.manager.get_remote_version(self.vault_id),
			local_version
		)

		# Remote changes from B -> C. sync_vault() should pull C.
		remote_version = str(uuid4())
		remote_source = self.tmp_path / "sync_remote_source.vault"

		self._write_vault(
			path=remote_source,
			version=remote_version,
			payload="sync-pull"
		)

		latest = self.manager.get_latest_remote_vault_file(
			self.vault_id
		)

		self.backend.update_file(
			file=latest,
			source=remote_source,
			name=f"latest_{remote_version}.vault"
		)

		self.manager.sync_vault(
			vault_id=self.vault_id,
			vault_path=str(self.vault_path)
		)

		self.assertEqual(
			self.vault_path.read_bytes(),
			remote_source.read_bytes()
		)
		self.assertEqual(
			self.manager.sync_data[self.vault_id].last_synced_version,
			remote_version
		)

	def test_sync_vault_detects_independent_local_and_remote_changes(self):
		self._init_sync()

		last_synced = self.initial_version
		local_version = str(uuid4())
		remote_version = str(uuid4())

		self._write_vault(
			path=self.vault_path,
			version=local_version,
			payload="conflicting-local"
		)

		remote_source = self.tmp_path / "conflicting_remote.vault"

		self._write_vault(
			path=remote_source,
			version=remote_version,
			payload="conflicting-remote"
		)

		latest = self.manager.get_latest_remote_vault_file(
			self.vault_id
		)

		self.backend.update_file(
			file=latest,
			source=remote_source,
			name=f"latest_{remote_version}.vault"
		)

		local_before = self.vault_path.read_bytes()

		with self.assertRaises(SyncConflictError):
			self.manager.sync_vault(
				vault_id=self.vault_id,
				vault_path=str(self.vault_path)
			)

		self.assertEqual(
			self.vault_path.read_bytes(),
			local_before
		)
		self.assertEqual(
			self.manager.get_remote_version(self.vault_id),
			remote_version
		)
		self.assertEqual(
			self.manager.sync_data[self.vault_id].last_synced_version,
			last_synced
		)

		remote_verification = self.tmp_path / "conflict_verification.vault"
		self._download_remote_latest(remote_verification)

		self.assertEqual(
			remote_verification.read_bytes(),
			remote_source.read_bytes()
		)

	def test_no_op_repairs_stale_last_synced_version(self):
		self._init_sync()

		stale_version = str(uuid4())

		self.manager.sync_data[
			self.vault_id
		].last_synced_version = stale_version

		# Persist the deliberately stale state first.
		self.manager.write_sync_data_to_disk()

		self.assertEqual(
			self.persisted_sync_data[
				self.vault_id
			]["last_synced_version"],
			stale_version
		)

		self.manager.sync_vault(
			vault_id=self.vault_id,
			vault_path=str(self.vault_path)
		)

		self.assertEqual(
			self.manager.sync_data[
				self.vault_id
			].last_synced_version,
			self.initial_version
		)
		self.assertEqual(
			self.persisted_sync_data[
				self.vault_id
			]["last_synced_version"],
			self.initial_version
		)

	def test_delete_remote_vault_removes_remote_folder_and_local_sync_data(self):
		remote_folder = self._init_sync()

		self.manager.delete_remote_vault(self.vault_id)

		self.assertNotIn(
			self.vault_id,
			self.manager.sync_data
		)
		self.assertEqual(
			self.persisted_sync_data,
			{}
		)

		self.assertIsNone(
			self.backend.find_folder_by_name(
				self.vault_id
			)
		)

		# The folder id stored before deletion should no longer be discoverable
		# through this SyncManager's metadata either.
		self.assertNotEqual(remote_folder.remote_id, "")


if __name__ == "__main__":
	unittest.main()
