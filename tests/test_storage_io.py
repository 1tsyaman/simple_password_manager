import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.pwd_manager import PwdManager
from storage.io import (
    create_and_load_vault,
    create_and_load_vault_for_gui,
    delete_vault,
    get_vault_list,
    load_vault,
    load_vault_for_gui,
    vault_exists,
    vault_exists_for_gui,
)


class StorageIoTests(unittest.TestCase):
    def test_load_vault_raises_when_path_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.vault"

            with self.assertRaises(FileNotFoundError):
                load_vault(str(path), "Master1!")

    def test_load_vault_delegates_to_pwd_manager_for_existing_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vault.vault"
            path.touch()
            manager = PwdManager()

            with patch(
                "storage.io.PwdManager.from_encrypted_file",
                return_value=manager,
            ) as loader:
                loaded = load_vault(str(path), "Master1!")

            self.assertIs(loaded, manager)
            loader.assert_called_once_with(str(path), "Master1!")

    def test_load_vault_for_gui_joins_directory_and_name(self):
        manager = PwdManager()

        with patch("storage.io.load_vault", return_value=manager) as loader:
            loaded = load_vault_for_gui("/app/data", "main.vault", "Master1!")

        self.assertIs(loaded, manager)
        loader.assert_called_once_with(
            path=os.path.join("/app/data", "main.vault"),
            pwd="Master1!",
        )

    def test_create_and_load_vault_touches_file_and_delegates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "new.vault"
            manager = PwdManager()

            with patch(
                "storage.io.PwdManager.pwd_manager_from_pwd",
                return_value=manager,
            ) as factory:
                loaded = create_and_load_vault(str(path), "Master1!")

            self.assertIs(loaded, manager)
            self.assertTrue(path.exists())
            factory.assert_called_once_with(str(path), "Master1!")

    def test_create_and_load_vault_rejects_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing-parent" / "vault.vault"

            with self.assertRaises(FileNotFoundError):
                create_and_load_vault(str(path), "Master1!")

    def test_create_and_load_vault_for_gui_adds_extension(self):
        manager = PwdManager()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "storage.io.create_and_load_vault",
                return_value=manager,
            ) as creator:
                loaded = create_and_load_vault_for_gui(
                    tmpdir,
                    "new-vault",
                    "Master1!",
                )

        self.assertIs(loaded, manager)
        creator.assert_called_once_with(
            path=str(Path(tmpdir) / "new-vault.vault"),
            pwd="Master1!",
        )

    def test_create_and_load_vault_for_gui_removes_created_file_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "broken.vault"

            def fail(path, pwd):
                Path(path).touch()
                raise OSError("failed")

            with patch("storage.io.create_and_load_vault", side_effect=fail):
                with self.assertRaises(OSError):
                    create_and_load_vault_for_gui(
                        tmpdir,
                        "broken",
                        "Master1!",
                    )

            self.assertFalse(path.exists())

    def test_get_vault_list_filters_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "one.vault").touch()
            Path(tmpdir, "two.vault").touch()
            Path(tmpdir, "notes.txt").touch()

            self.assertCountEqual(
                get_vault_list(tmpdir),
                ["one.vault", "two.vault"],
            )

    def test_vault_exists_matches_path_existence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vault.vault"

            self.assertFalse(vault_exists(str(path)))
            path.touch()
            self.assertTrue(vault_exists(str(path)))

    def test_vault_exists_for_gui_adds_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "main.vault"

            self.assertFalse(vault_exists_for_gui(tmpdir, "main"))
            path.touch()
            self.assertTrue(vault_exists_for_gui(tmpdir, "main"))

    def test_delete_vault_removes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "vault.vault"
            path.touch()

            delete_vault(str(path))

            self.assertFalse(path.exists())

    def test_delete_vault_propagates_oserror_for_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(OSError):
                delete_vault(tmpdir)


if __name__ == "__main__":
    unittest.main()
