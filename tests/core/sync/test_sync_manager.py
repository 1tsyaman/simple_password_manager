from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import UUID

import core.sync.sync_manager as sync_manager_module
from core.sync.backend import CloudBackend, RemoteFile, RemoteFolder
from core.sync.errors import (
	ClientCredentialsNotFoundError,
	NoVaultSyncDataError,
	CloudBackendError,
	RemoteVaultNotFoundError,
	VaultSyncDataExistsError,
	SyncRollbackError,
	SyncConflictError,
	CloudVaultAuthenticityError,
	HttpError,
)
from core.etc.errors import IllegalArgumentError
from core.etc.types import VaultSyncData, SyncActions
from core.sync.sync_manager import (
	SyncManager,
	SyncCallbacks,
	_get_version_from_vault_name,
	_is_valid_version,
	_file_has_valid_latest_format,
)


VERSION_A = "11111111-1111-4111-8111-111111111111"
VERSION_B = "22222222-2222-4222-8222-222222222222"
VERSION_C = "33333333-3333-4333-8333-333333333333"

VAULT_ID = "vault-id"
REMOTE_FOLDER_ID = "remote-folder-id"
VAULT_PATH = "vaults/test.vault"


def make_remote_file(
	version: str = VERSION_A,
	modified_time: datetime | None = None,
	remote_id: str = "remote-file-id",
) -> RemoteFile:
	if modified_time is None:
		modified_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

	return RemoteFile(
		remote_id=remote_id,
		name=f"latest_{version}.vault",
		modified_time=modified_time,
	)


class SyncManagerTestCase(TestCase):
	def setUp(self) -> None:
		self.backend = MagicMock(spec=CloudBackend)
		self.writeback = MagicMock()
		self.local_version_getter = MagicMock(return_value=VERSION_A)
		self.vault_auth_checker = MagicMock(return_value=True)
		self.lock = RLock()
		self.download_path = Path("downloads")

		self.sync_data = {
			VAULT_ID: VaultSyncData(
				remote_folder_id=REMOTE_FOLDER_ID,
				last_synced_version=VERSION_A,
			)
		}

		callbacks = SyncCallbacks(
			sync_data_writeback=self.writeback,
			local_version_getter=self.local_version_getter,
			vault_auth_checker=self.vault_auth_checker,
		)

		self.manager = SyncManager(
			backend=self.backend,
			download_path=self.download_path,
			sync_data=self.sync_data,
			sync_callbacks=callbacks,
			lock=self.lock,
		)

	# ------------------------------------------------------------------
	# pull_vault
	# ------------------------------------------------------------------

	def test_pull_vault_pull_dispatches_to_internal_pull(self) -> None:
		latest = make_remote_file(VERSION_B)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.PULL, VERSION_A, VERSION_B),
			),
			patch.object(self.manager, "_pull_vault") as pull,
		):
			self.manager.pull_vault(VAULT_ID, VAULT_PATH)

		pull.assert_called_once_with(
			vault_id=VAULT_ID,
			vault_path=VAULT_PATH,
			vault_file=latest,
			remote_version=VERSION_B,
		)

	def test_pull_vault_no_op_updates_sync_data(self) -> None:
		latest = make_remote_file(VERSION_A)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.NO_OP, VERSION_A, VERSION_A),
			),
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			self.manager.pull_vault(VAULT_ID, VAULT_PATH)

		update.assert_called_once_with(
			vault_id=VAULT_ID,
			local_version=VERSION_A,
		)

	def test_pull_vault_push_decision_does_nothing(self) -> None:
		latest = make_remote_file(VERSION_A)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.PUSH, VERSION_B, VERSION_A),
			),
			patch.object(self.manager, "_pull_vault") as pull,
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			self.manager.pull_vault(VAULT_ID, VAULT_PATH)

		pull.assert_not_called()
		update.assert_not_called()

	def test_pull_vault_conflict_raises(self) -> None:
		latest = make_remote_file(VERSION_C)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.CONFLICT, VERSION_B, VERSION_C),
			),
		):
			with self.assertRaises(SyncConflictError):
				self.manager.pull_vault(VAULT_ID, VAULT_PATH)

	def test_pull_vault_missing_sync_data_is_translated(self) -> None:
		with patch.object(
			self.manager,
			"get_latest_remote_vault_file",
			side_effect=NoVaultSyncDataError,
		):
			with self.assertRaises(IllegalArgumentError):
				self.manager.pull_vault(VAULT_ID, VAULT_PATH)

	# ------------------------------------------------------------------
	# push_vault
	# ------------------------------------------------------------------

	def test_push_vault_push_dispatches_to_internal_push(self) -> None:
		latest = make_remote_file(VERSION_A)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.PUSH, VERSION_B, VERSION_A),
			),
			patch.object(self.manager, "_push_vault") as push,
		):
			self.manager.push_vault(VAULT_ID, VAULT_PATH)

		push.assert_called_once_with(
			vault_id=VAULT_ID,
			vault_path=VAULT_PATH,
			vault_file=latest,
			local_version=VERSION_B,
		)

	def test_push_vault_no_op_updates_sync_data(self) -> None:
		latest = make_remote_file(VERSION_A)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.NO_OP, VERSION_A, VERSION_A),
			),
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			self.manager.push_vault(VAULT_ID, VAULT_PATH)

		update.assert_called_once_with(
			vault_id=VAULT_ID,
			local_version=VERSION_A,
		)

	def test_push_vault_pull_decision_does_nothing(self) -> None:
		latest = make_remote_file(VERSION_B)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.PULL, VERSION_A, VERSION_B),
			),
			patch.object(self.manager, "_push_vault") as push,
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			self.manager.push_vault(VAULT_ID, VAULT_PATH)

		push.assert_not_called()
		update.assert_not_called()

	def test_push_vault_conflict_raises(self) -> None:
		latest = make_remote_file(VERSION_C)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.CONFLICT, VERSION_B, VERSION_C),
			),
		):
			with self.assertRaises(SyncConflictError):
				self.manager.push_vault(VAULT_ID, VAULT_PATH)

	def test_push_vault_missing_sync_data_is_translated(self) -> None:
		with patch.object(
			self.manager,
			"get_latest_remote_vault_file",
			side_effect=NoVaultSyncDataError,
		):
			with self.assertRaises(IllegalArgumentError):
				self.manager.push_vault(VAULT_ID, VAULT_PATH)

	# ------------------------------------------------------------------
	# sync_vault
	# ------------------------------------------------------------------

	def test_sync_vault_pull_dispatches_to_internal_pull(self) -> None:
		latest = make_remote_file(VERSION_B)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.PULL, VERSION_A, VERSION_B),
			),
			patch.object(self.manager, "_pull_vault") as pull,
		):
			self.manager.sync_vault(VAULT_ID, VAULT_PATH)

		pull.assert_called_once_with(
			vault_id=VAULT_ID,
			vault_path=VAULT_PATH,
			vault_file=latest,
			remote_version=VERSION_B,
		)

	def test_sync_vault_push_dispatches_to_internal_push(self) -> None:
		latest = make_remote_file(VERSION_A)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.PUSH, VERSION_B, VERSION_A),
			),
			patch.object(self.manager, "_push_vault") as push,
		):
			self.manager.sync_vault(VAULT_ID, VAULT_PATH)

		push.assert_called_once_with(
			vault_id=VAULT_ID,
			vault_path=VAULT_PATH,
			vault_file=latest,
			local_version=VERSION_B,
		)

	def test_sync_vault_no_op_updates_sync_data(self) -> None:
		latest = make_remote_file(VERSION_A)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.NO_OP, VERSION_A, VERSION_A),
			),
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			self.manager.sync_vault(VAULT_ID, VAULT_PATH)

		update.assert_called_once_with(
			vault_id=VAULT_ID,
			local_version=VERSION_A,
		)

	def test_sync_vault_conflict_raises(self) -> None:
		latest = make_remote_file(VERSION_C)

		with (
			patch.object(self.manager, "get_latest_remote_vault_file", return_value=latest),
			patch.object(
				self.manager,
				"_decide_sync_action",
				return_value=(SyncActions.CONFLICT, VERSION_B, VERSION_C),
			),
		):
			with self.assertRaises(SyncConflictError):
				self.manager.sync_vault(VAULT_ID, VAULT_PATH)

	def test_sync_vault_missing_sync_data_is_translated(self) -> None:
		with patch.object(
			self.manager,
			"get_latest_remote_vault_file",
			side_effect=NoVaultSyncDataError,
		):
			with self.assertRaises(IllegalArgumentError):
				self.manager.sync_vault(VAULT_ID, VAULT_PATH)

	# ------------------------------------------------------------------
	# init_vault_sync
	# ------------------------------------------------------------------

	def test_init_vault_sync_success(self) -> None:
		self.manager.sync_data.clear()
		remote_folder = RemoteFolder(
			remote_id=REMOTE_FOLDER_ID,
			name=VAULT_ID,
		)
		self.backend.create_folder.return_value = remote_folder
		self.local_version_getter.return_value = VERSION_A

		self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

		self.backend.create_folder.assert_called_once_with(VAULT_ID)
		self.backend.upload_file.assert_called_once_with(
			remote_name=f"latest_{VERSION_A}.vault",
			source=Path(VAULT_PATH),
			parent=remote_folder,
		)
		self.assertEqual(
			self.manager.sync_data[VAULT_ID],
			VaultSyncData(
				remote_folder_id=REMOTE_FOLDER_ID,
				last_synced_version=VERSION_A,
			),
		)
		self.writeback.assert_called_once_with({
			VAULT_ID: {
				"remote_folder_id": REMOTE_FOLDER_ID,
				"last_synced_version": VERSION_A,
			}
		})

	def test_init_vault_sync_existing_data_raises(self) -> None:
		with self.assertRaises(VaultSyncDataExistsError):
			self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

		self.backend.create_folder.assert_not_called()

	def test_init_vault_sync_folder_creation_error_is_translated(self) -> None:
		self.manager.sync_data.clear()
		self.backend.create_folder.side_effect = HttpError

		with self.assertRaises(CloudBackendError):
			self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

		self.backend.upload_file.assert_not_called()

	def test_init_vault_sync_upload_error_rolls_back(self) -> None:
		self.manager.sync_data.clear()
		remote_folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)
		self.backend.create_folder.return_value = remote_folder
		self.backend.upload_file.side_effect = HttpError

		with patch.object(self.manager, "_cleanup_vault_init") as cleanup:
			with self.assertRaises(CloudBackendError):
				self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

		cleanup.assert_called_once_with(
			vault_id=VAULT_ID,
			remote_folder=remote_folder,
		)

	def test_init_vault_sync_upload_error_and_rollback_error_raises_sync_rollback(self) -> None:
		self.manager.sync_data.clear()
		remote_folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)
		self.backend.create_folder.return_value = remote_folder
		self.backend.upload_file.side_effect = HttpError

		with patch.object(
			self.manager,
			"_cleanup_vault_init",
			side_effect=CloudBackendError,
		):
			with self.assertRaises(SyncRollbackError):
				self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

	def test_init_vault_sync_write_error_rolls_back_and_reraises(self) -> None:
		self.manager.sync_data.clear()
		remote_folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)
		self.backend.create_folder.return_value = remote_folder
		self.writeback.side_effect = OSError("write failed")

		with patch.object(self.manager, "_cleanup_vault_init") as cleanup:
			with self.assertRaises(OSError):
				self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

		cleanup.assert_called_once_with(
			vault_id=VAULT_ID,
			remote_folder=remote_folder,
		)

	def test_init_vault_sync_write_error_and_rollback_error_raises_sync_rollback(self) -> None:
		self.manager.sync_data.clear()
		remote_folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)
		self.backend.create_folder.return_value = remote_folder
		self.writeback.side_effect = OSError("write failed")

		with patch.object(
			self.manager,
			"_cleanup_vault_init",
			side_effect=CloudBackendError,
		):
			with self.assertRaises(SyncRollbackError):
				self.manager.init_vault_sync(VAULT_ID, VAULT_PATH)

	# ------------------------------------------------------------------
	# delete_remote_vault
	# ------------------------------------------------------------------

	def test_delete_remote_vault_success(self) -> None:
		self.manager.delete_remote_vault(VAULT_ID)

		self.assertNotIn(VAULT_ID, self.manager.sync_data)
		self.writeback.assert_called_once_with({})
		self.backend.delete_folder_recursive.assert_called_once_with(
			RemoteFolder(
				remote_id=REMOTE_FOLDER_ID,
				name=VAULT_ID,
			)
		)

	def test_delete_remote_vault_unknown_vault_raises(self) -> None:
		self.manager.sync_data.clear()

		with self.assertRaises(IllegalArgumentError):
			self.manager.delete_remote_vault(VAULT_ID)

	def test_delete_remote_vault_write_failure_restores_memory(self) -> None:
		original = self.manager.sync_data[VAULT_ID]
		self.writeback.side_effect = OSError("write failed")

		with self.assertRaises(OSError):
			self.manager.delete_remote_vault(VAULT_ID)

		self.assertIs(self.manager.sync_data[VAULT_ID], original)
		self.backend.delete_folder_recursive.assert_not_called()

	def test_delete_remote_vault_remote_failure_restores_sync_data(self) -> None:
		original = self.manager.sync_data[VAULT_ID]
		self.backend.delete_folder_recursive.side_effect = HttpError

		with self.assertRaises(CloudBackendError):
			self.manager.delete_remote_vault(VAULT_ID)

		self.assertIs(self.manager.sync_data[VAULT_ID], original)
		self.assertEqual(self.writeback.call_count, 2)
		self.assertEqual(self.writeback.call_args_list[0].args[0], {})
		self.assertEqual(
			self.writeback.call_args_list[1].args[0],
			{
				VAULT_ID: {
					"remote_folder_id": REMOTE_FOLDER_ID,
					"last_synced_version": VERSION_A,
				}
			},
		)

	def test_delete_remote_vault_remote_failure_and_rollback_write_failure(self) -> None:
		self.backend.delete_folder_recursive.side_effect = HttpError
		self.writeback.side_effect = [None, OSError("rollback failed")]

		with self.assertRaises(SyncRollbackError):
			self.manager.delete_remote_vault(VAULT_ID)

		self.assertIn(VAULT_ID, self.manager.sync_data)

	# ------------------------------------------------------------------
	# remote/local lookup and persistence helpers
	# ------------------------------------------------------------------

	def test_get_latest_remote_vault_file_success(self) -> None:
		latest = make_remote_file(VERSION_A)
		self.backend.list_files.return_value = [latest]

		result = self.manager.get_latest_remote_vault_file(VAULT_ID)

		self.assertEqual(result, latest)
		self.backend.list_files.assert_called_once_with(
			RemoteFolder(
				remote_id=REMOTE_FOLDER_ID,
				name=VAULT_ID,
			)
		)

	def test_get_latest_remote_vault_file_missing_sync_data(self) -> None:
		self.manager.sync_data.clear()

		with self.assertRaises(NoVaultSyncDataError):
			self.manager.get_latest_remote_vault_file(VAULT_ID)

	def test_get_latest_remote_vault_file_no_remote_vault(self) -> None:
		self.backend.list_files.return_value = []

		with self.assertRaises(RemoteVaultNotFoundError):
			self.manager.get_latest_remote_vault_file(VAULT_ID)

	def test_get_latest_remote_vault_file_http_error_is_translated(self) -> None:
		self.backend.list_files.side_effect = HttpError

		with self.assertRaises(CloudBackendError):
			self.manager.get_latest_remote_vault_file(VAULT_ID)

	def test_get_remote_version(self) -> None:
		latest = make_remote_file(VERSION_B)

		with patch.object(
			self.manager,
			"get_latest_remote_vault_file",
			return_value=latest,
		):
			self.assertEqual(
				self.manager.get_remote_version(VAULT_ID),
				VERSION_B,
			)

	def test_get_local_version_uses_callback(self) -> None:
		self.local_version_getter.return_value = VERSION_B

		result = self.manager.get_local_version(VAULT_ID)

		self.assertEqual(result, VERSION_B)
		self.local_version_getter.assert_called_once_with(VAULT_ID)

	def test_write_sync_data_to_disk_serializes_data(self) -> None:
		self.manager.write_sync_data_to_disk()

		self.writeback.assert_called_once_with({
			VAULT_ID: {
				"remote_folder_id": REMOTE_FOLDER_ID,
				"last_synced_version": VERSION_A,
			}
		})

	def test_write_sync_data_to_disk_propagates_oserror(self) -> None:
		self.writeback.side_effect = OSError("write failed")

		with self.assertRaises(OSError):
			self.manager.write_sync_data_to_disk()

	def test_get_remote_folder_id_success(self) -> None:
		folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)
		self.backend.find_folder_by_name.return_value = folder

		result = self.manager.get_remote_folder_id(VAULT_ID)

		self.assertEqual(result, REMOTE_FOLDER_ID)
		self.backend.find_folder_by_name.assert_called_once_with(VAULT_ID)

	def test_get_remote_folder_id_missing_folder_raises(self) -> None:
		self.backend.find_folder_by_name.return_value = None

		with self.assertRaises(RemoteVaultNotFoundError):
			self.manager.get_remote_folder_id(VAULT_ID)

	def test_get_remote_folder_id_http_error_is_translated(self) -> None:
		self.backend.find_folder_by_name.side_effect = HttpError

		with self.assertRaises(CloudBackendError):
			self.manager.get_remote_folder_id(VAULT_ID)

	def test_sync_data_to_dict(self) -> None:
		self.manager.sync_data["vault-2"] = VaultSyncData(
			remote_folder_id="remote-folder-2",
			last_synced_version=None,
		)

		self.assertEqual(
			self.manager._sync_data_to_dict(),
			{
				VAULT_ID: {
					"remote_folder_id": REMOTE_FOLDER_ID,
					"last_synced_version": VERSION_A,
				},
				"vault-2": {
					"remote_folder_id": "remote-folder-2",
					"last_synced_version": None,
				},
			},
		)

	# ------------------------------------------------------------------
	# cleanup and decision helpers
	# ------------------------------------------------------------------

	def test_cleanup_vault_init_removes_sync_data_and_remote_folder(self) -> None:
		folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)

		self.manager._cleanup_vault_init(VAULT_ID, folder)

		self.assertNotIn(VAULT_ID, self.manager.sync_data)
		self.backend.delete_folder_recursive.assert_called_once_with(folder)

	def test_cleanup_vault_init_http_error_is_translated(self) -> None:
		folder = RemoteFolder(remote_id=REMOTE_FOLDER_ID, name=VAULT_ID)
		self.backend.delete_folder_recursive.side_effect = HttpError

		with self.assertRaises(CloudBackendError):
			self.manager._cleanup_vault_init(VAULT_ID, folder)

		self.assertNotIn(VAULT_ID, self.manager.sync_data)

	def test_decide_sync_action_no_op(self) -> None:
		self.local_version_getter.return_value = VERSION_A
		self.manager.sync_data[VAULT_ID].last_synced_version = VERSION_C
		latest = make_remote_file(VERSION_A)

		result = self.manager._decide_sync_action(VAULT_ID, latest)

		self.assertEqual(result, (SyncActions.NO_OP, VERSION_A, VERSION_A))

	def test_decide_sync_action_pull(self) -> None:
		self.local_version_getter.return_value = VERSION_A
		self.manager.sync_data[VAULT_ID].last_synced_version = VERSION_A
		latest = make_remote_file(VERSION_B)

		result = self.manager._decide_sync_action(VAULT_ID, latest)

		self.assertEqual(result, (SyncActions.PULL, VERSION_A, VERSION_B))

	def test_decide_sync_action_push(self) -> None:
		self.local_version_getter.return_value = VERSION_B
		self.manager.sync_data[VAULT_ID].last_synced_version = VERSION_A
		latest = make_remote_file(VERSION_A)

		result = self.manager._decide_sync_action(VAULT_ID, latest)

		self.assertEqual(result, (SyncActions.PUSH, VERSION_B, VERSION_A))

	def test_decide_sync_action_conflict(self) -> None:
		self.local_version_getter.return_value = VERSION_B
		self.manager.sync_data[VAULT_ID].last_synced_version = VERSION_A
		latest = make_remote_file(VERSION_C)

		result = self.manager._decide_sync_action(VAULT_ID, latest)

		self.assertEqual(result, (SyncActions.CONFLICT, VERSION_B, VERSION_C))

	def test_decide_sync_action_missing_sync_data_raises(self) -> None:
		self.manager.sync_data.clear()
		latest = make_remote_file(VERSION_A)

		with self.assertRaises(IllegalArgumentError):
			self.manager._decide_sync_action(VAULT_ID, latest)

	# ------------------------------------------------------------------
	# internal pull/push
	# ------------------------------------------------------------------

	def test_internal_pull_success(self) -> None:
		latest = make_remote_file(VERSION_B)
		expected_download_path = self.download_path / Path(VAULT_PATH).name

		with (
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
			patch.object(sync_manager_module.io, "move_file") as move_file,
		):
			self.manager._pull_vault(
				vault_id=VAULT_ID,
				vault_path=VAULT_PATH,
				vault_file=latest,
				remote_version=VERSION_B,
			)

		self.backend.download_file_atomic.assert_called_once_with(
			file=latest,
			destination=expected_download_path,
		)
		self.vault_auth_checker.assert_called_once_with(VAULT_ID)
		move_file.assert_called_once_with(str(expected_download_path), VAULT_PATH)
		update.assert_called_once_with(
			vault_id=VAULT_ID,
			local_version=VERSION_B,
		)

	def test_internal_pull_http_error_is_translated(self) -> None:
		latest = make_remote_file(VERSION_B)
		self.backend.download_file_atomic.side_effect = HttpError

		with self.assertRaises(CloudBackendError):
			self.manager._pull_vault(
				VAULT_ID,
				VAULT_PATH,
				latest,
				VERSION_B,
			)

		self.vault_auth_checker.assert_not_called()

	def test_internal_pull_auth_failure_deletes_download_and_raises(self) -> None:
		latest = make_remote_file(VERSION_B)
		self.vault_auth_checker.return_value = False
		expected_download_path = self.download_path / Path(VAULT_PATH).name

		with (
			patch.object(sync_manager_module.io, "delete_file") as delete_file,
			patch.object(sync_manager_module.io, "move_file") as move_file,
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			with self.assertRaises(CloudVaultAuthenticityError):
				self.manager._pull_vault(
					VAULT_ID,
					VAULT_PATH,
					latest,
					VERSION_B,
				)

		delete_file.assert_called_once_with(str(expected_download_path))
		move_file.assert_not_called()
		update.assert_not_called()

	def test_internal_pull_auth_failure_ignores_cleanup_oserror(self) -> None:
		latest = make_remote_file(VERSION_B)
		self.vault_auth_checker.return_value = False

		with patch.object(
			sync_manager_module.io,
			"delete_file",
			side_effect=OSError("cleanup failed"),
		):
			with self.assertRaises(CloudVaultAuthenticityError):
				self.manager._pull_vault(
					VAULT_ID,
					VAULT_PATH,
					latest,
					VERSION_B,
				)

	def test_internal_pull_move_failure_does_not_update_sync_data(self) -> None:
		latest = make_remote_file(VERSION_B)

		with (
			patch.object(
				sync_manager_module.io,
				"move_file",
				side_effect=OSError("move failed"),
			),
			patch.object(self.manager, "_update_sync_data_if_necessary") as update,
		):
			with self.assertRaises(OSError):
				self.manager._pull_vault(
					VAULT_ID,
					VAULT_PATH,
					latest,
					VERSION_B,
				)

		update.assert_not_called()

	def test_internal_push_success(self) -> None:
		latest = make_remote_file(VERSION_A)

		with patch.object(self.manager, "_update_sync_data_if_necessary") as update:
			self.manager._push_vault(
				vault_id=VAULT_ID,
				vault_path=VAULT_PATH,
				vault_file=latest,
				local_version=VERSION_B,
			)

		self.backend.update_file.assert_called_once_with(
			file=latest,
			source=Path(VAULT_PATH),
			name=f"latest_{VERSION_B}.vault",
		)
		update.assert_called_once_with(
			vault_id=VAULT_ID,
			local_version=VERSION_B,
		)

	def test_internal_push_http_error_is_translated_and_does_not_update_metadata(self) -> None:
		latest = make_remote_file(VERSION_A)
		self.backend.update_file.side_effect = HttpError

		with patch.object(self.manager, "_update_sync_data_if_necessary") as update:
			with self.assertRaises(CloudBackendError):
				self.manager._push_vault(
					VAULT_ID,
					VAULT_PATH,
					latest,
					VERSION_B,
				)

		update.assert_not_called()

	def test_update_sync_data_if_necessary_writes_when_changed(self) -> None:
		self.manager._update_sync_data_if_necessary(VAULT_ID, VERSION_B)

		self.assertEqual(
			self.manager.sync_data[VAULT_ID].last_synced_version,
			VERSION_B,
		)
		self.writeback.assert_called_once_with({
			VAULT_ID: {
				"remote_folder_id": REMOTE_FOLDER_ID,
				"last_synced_version": VERSION_B,
			}
		})

	def test_update_sync_data_if_necessary_does_not_write_when_unchanged(self) -> None:
		self.manager._update_sync_data_if_necessary(VAULT_ID, VERSION_A)

		self.writeback.assert_not_called()

	def test_update_sync_data_if_necessary_write_error_leaves_memory_updated(self) -> None:
		self.writeback.side_effect = OSError("write failed")

		with self.assertRaises(OSError):
			self.manager._update_sync_data_if_necessary(VAULT_ID, VERSION_B)

		self.assertEqual(
			self.manager.sync_data[VAULT_ID].last_synced_version,
			VERSION_B,
		)

	# ------------------------------------------------------------------
	# static factory / utility methods
	# ------------------------------------------------------------------

	def test_get_fresh_version_returns_unique_uuid4(self) -> None:
		first = SyncManager.get_fresh_version()
		second = SyncManager.get_fresh_version()

		self.assertEqual(UUID(first).version, 4)
		self.assertEqual(UUID(second).version, 4)
		self.assertNotEqual(first, second)

	def test_from_google_drive_token_missing_credentials_raises(self) -> None:
		with TemporaryDirectory() as tmp:
			missing_credentials = Path(tmp) / "missing.json"

			with self.assertRaises(ClientCredentialsNotFoundError):
				callbacks = SyncCallbacks(
					sync_data_writeback=self.writeback,
					local_version_getter=self.local_version_getter,
					vault_auth_checker=self.vault_auth_checker,
				)
				SyncManager.from_google_drive_token(
					client_credentials_path=str(missing_credentials),
					token_path=str(Path(tmp) / "token.json"),
					download_path=str(Path(tmp) / "downloads"),
					sync_data={},
					sync_callbacks=callbacks,
					sync_lock=self.lock,
				)

	def test_from_google_drive_token_builds_manager_without_real_auth(self) -> None:
		with TemporaryDirectory() as tmp:
			tmp_path = Path(tmp)
			credentials_path = tmp_path / "credentials.json"
			credentials_path.write_text("{}", encoding="utf-8")
			token_path = tmp_path / "token.json"
			download_path = tmp_path / "downloads"
			raw_sync_data = {
				VAULT_ID: {
					"remote_folder_id": REMOTE_FOLDER_ID,
					"last_synced_version": VERSION_A,
				}
			}
			credentials = object()
			backend = MagicMock(spec=CloudBackend)

			with (
				patch.object(
					sync_manager_module.desktop_auth,
					"get_credentials",
					return_value=credentials,
				) as get_credentials,
				patch.object(
					sync_manager_module,
					"GoogleDriveBackend",
					return_value=backend,
				) as backend_cls,
			):
				callbacks = SyncCallbacks(
					sync_data_writeback=self.writeback,
					local_version_getter=self.local_version_getter,
					vault_auth_checker=self.vault_auth_checker,
				)
				manager = SyncManager.from_google_drive_token(
					client_credentials_path=str(credentials_path),
					token_path=str(token_path),
					download_path=str(download_path),
					sync_data=raw_sync_data,
					sync_callbacks=callbacks,
					sync_lock=self.lock,
				)

			get_credentials.assert_called_once_with(
				client_credentials_path=credentials_path,
				token_path=token_path,
			)
			backend_cls.assert_called_once_with(credentials)
			self.assertTrue(download_path.is_dir())
			self.assertIs(manager.backend, backend)
			self.assertEqual(manager.download_path, download_path)
			self.assertEqual(
				manager.sync_data,
				{
					VAULT_ID: VaultSyncData(
						remote_folder_id=REMOTE_FOLDER_ID,
						last_synced_version=VERSION_A,
					)
				},
			)
			self.assertIs(manager._sync_data_writeback, self.writeback)
			self.assertIs(manager.local_version_getter, self.local_version_getter)
			self.assertIs(manager.vault_auth_checker, self.vault_auth_checker)
			self.assertIs(manager.lock, self.lock)

	def test_from_google_drive_token_invalid_sync_data_raises(self) -> None:
		with TemporaryDirectory() as tmp:
			tmp_path = Path(tmp)
			credentials_path = tmp_path / "credentials.json"
			credentials_path.write_text("{}", encoding="utf-8")

			with (
				patch.object(
					sync_manager_module.desktop_auth,
					"get_credentials",
					return_value=object(),
				),
				patch.object(sync_manager_module, "GoogleDriveBackend"),
			):
				with self.assertRaises(IllegalArgumentError):
					callbacks = SyncCallbacks(
						sync_data_writeback=self.writeback,
						local_version_getter=self.local_version_getter,
						vault_auth_checker=self.vault_auth_checker,
					)
					SyncManager.from_google_drive_token(
						client_credentials_path=str(credentials_path),
						token_path=str(tmp_path / "token.json"),
						download_path=str(tmp_path / "downloads"),
						sync_data={
							VAULT_ID: {
								"remote_folder_id": REMOTE_FOLDER_ID,
								# missing last_synced_version
							}
						},
						sync_callbacks=callbacks,
						sync_lock=self.lock,
					)

	# ------------------------------------------------------------------
	# latest-file selection and module helpers
	# ------------------------------------------------------------------

	def test_get_latest_vault_file_returns_none_when_no_valid_file_exists(self) -> None:
		files = [
			RemoteFile(
				remote_id="1",
				name="backup_not-a-version.vault",
				modified_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
			),
			RemoteFile(
				remote_id="2",
				name="latest_not-a-uuid.vault",
				modified_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
			),
		]

		self.assertIsNone(SyncManager._get_latest_vault_file(files))

	def test_get_latest_vault_file_returns_only_valid_file(self) -> None:
		valid = make_remote_file(VERSION_A)
		invalid = RemoteFile(
			remote_id="invalid",
			name="latest_not-a-uuid.vault",
			modified_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
		)

		self.assertEqual(
			SyncManager._get_latest_vault_file([invalid, valid]),
			valid,
		)

	def test_get_latest_vault_file_returns_newest_valid_file(self) -> None:
		older = make_remote_file(
			VERSION_A,
			datetime(2026, 1, 1, tzinfo=timezone.utc),
			"old",
		)
		newer = make_remote_file(
			VERSION_B,
			datetime(2026, 1, 2, tzinfo=timezone.utc),
			"new",
		)

		self.assertEqual(
			SyncManager._get_latest_vault_file([older, newer]),
			newer,
		)

	def test_get_version_from_vault_name(self) -> None:
		self.assertEqual(
			_get_version_from_vault_name(f"latest_{VERSION_A}.vault"),
			VERSION_A,
		)

	def test_is_valid_version_accepts_uuid4(self) -> None:
		self.assertTrue(_is_valid_version(VERSION_A))

	def test_is_valid_version_rejects_non_uuid4(self) -> None:
		self.assertFalse(_is_valid_version("550e8400-e29b-11d4-a716-446655440000"))

	def test_is_valid_version_rejects_malformed_uuid(self) -> None:
		self.assertFalse(_is_valid_version("not-a-uuid"))

	def test_file_has_valid_latest_format_accepts_valid_name(self) -> None:
		self.assertTrue(
			_file_has_valid_latest_format(f"latest_{VERSION_A}.vault")
		)

	def test_file_has_valid_latest_format_rejects_wrong_prefix(self) -> None:
		self.assertFalse(
			_file_has_valid_latest_format(f"backup_{VERSION_A}.vault")
		)

	def test_file_has_valid_latest_format_rejects_wrong_suffix(self) -> None:
		self.assertFalse(
			_file_has_valid_latest_format(f"latest_{VERSION_A}.json")
		)

	def test_file_has_valid_latest_format_rejects_invalid_uuid(self) -> None:
		self.assertFalse(
			_file_has_valid_latest_format("latest_not-a-uuid.vault")
		)


if __name__ == "__main__":
	import unittest
	unittest.main()
