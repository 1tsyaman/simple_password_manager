import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from storage.io import (
    INVALID_PATH_ERROR,
    create_and_load_vault,
    delete_vault,
    load_vault,
    vault_exists,
)
from tests.helpers import VALID_MASTER_PASSWORD


class StorageIOTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.path = self.root / "vault.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_load_vault_creates_file(self):
        manager = create_and_load_vault(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(manager)
        self.assertTrue(self.path.exists())
        self.assertTrue(vault_exists(str(self.path)))

    def test_create_and_load_vault_rejects_invalid_parent(self):
        path = self.root / "missing" / "vault.json"
        with self.assertRaisesRegex(FileNotFoundError, INVALID_PATH_ERROR):
            create_and_load_vault(str(path), VALID_MASTER_PASSWORD)

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_load_vault_reads_saved_entries(self, _sleep):
        manager = create_and_load_vault(str(self.path), VALID_MASTER_PASSWORD)
        manager.add_entry("example.com", "alice", "secret", "")  # type: ignore[union-attr]
        manager.encrypt()  # type: ignore[union-attr]
        restored = load_vault(str(self.path), VALID_MASTER_PASSWORD)
        self.assertEqual(restored.get_password("example.com", "alice"), "secret")  # type: ignore[union-attr]

    def test_load_missing_vault_returns_none(self):
        self.assertIsNone(load_vault(str(self.path), VALID_MASTER_PASSWORD))

    def test_delete_vault(self):
        self.path.touch()
        delete_vault(str(self.path))
        self.assertFalse(self.path.exists())

    def test_delete_missing_vault_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            delete_vault(str(self.path))

    def test_delete_directory_raises_os_error(self):
        directory = self.root / "directory"
        directory.mkdir()
        with self.assertRaisesRegex(OSError, "directory"):
            delete_vault(str(directory))
