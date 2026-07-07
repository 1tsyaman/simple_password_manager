import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.pwd_manager import PwdManager
from storage.io import INVALID_PATH_ERROR, create_and_load_vault, delete_vault, load_vault, vault_exists


class StorageIoTests(unittest.TestCase):
	def test_load_vault_returns_none_when_path_does_not_exist(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "missing.vault"

			with patch("builtins.print"):
				self.assertIsNone(load_vault(str(path)))

	def test_load_vault_delegates_to_pwd_manager_for_existing_path(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "vault.vault"
			path.touch()
			manager = PwdManager()

			with patch("storage.io.PwdManager.from_encrypted_file", return_value=manager) as loader:
				self.assertIs(load_vault(str(path)), manager)

			loader.assert_called_once_with(str(path))

	def test_create_and_load_vault_touches_file_and_delegates(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "new.vault"
			manager = PwdManager()

			with patch("storage.io.PwdManager.pwd_manager_from_pwd", return_value=manager) as factory:
				self.assertIs(create_and_load_vault(str(path)), manager)

			self.assertTrue(path.exists())
			factory.assert_called_once_with(str(path))

	def test_create_and_load_vault_rejects_missing_parent_directory(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "missing-parent" / "vault.vault"

			with self.assertRaisesRegex(FileNotFoundError, INVALID_PATH_ERROR):
				create_and_load_vault(str(path))

	def test_vault_exists_matches_path_existence(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "vault.vault"

			self.assertFalse(vault_exists(str(path)))
			path.touch()
			self.assertTrue(vault_exists(str(path)))

	def test_delete_vault_removes_file(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			path = Path(tmpdir) / "vault.vault"
			path.touch()

			delete_vault(str(path))

			self.assertFalse(path.exists())

	def test_delete_vault_raises_oserror_for_directory(self):
		with tempfile.TemporaryDirectory() as tmpdir:
			with self.assertRaisesRegex(OSError, "Given vault path is a directory"):
				delete_vault(tmpdir)


if __name__ == "__main__":
	unittest.main()
