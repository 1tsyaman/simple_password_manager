import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.errors import VaultFormatError
from core.pwd_manager import PwdManager
from tests.helpers import VALID_MASTER_PASSWORD, write_main_branch_vault


class VaultMigrationTests(unittest.TestCase):
    def test_loads_pre_totp_main_branch_vault(self):
        old_data = {
            "github.com, yaman, personal": "github-password",
            "example.com, alice, work": "example-password",
        }

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.vault"
            write_main_branch_vault(path, old_data)

            manager = PwdManager.from_encrypted_file(
                str(path),
                VALID_MASTER_PASSWORD,
            )

        self.assertEqual(manager.get_entry_list_len(), 2)
        self.assertEqual(
            manager.get_password("github.com", "yaman"),
            "github-password",
        )
        self.assertEqual(
            manager.get_password("example.com", "alice"),
            "example-password",
        )
        self.assertFalse(manager.has_totp("github.com", "yaman"))
        self.assertFalse(manager.has_totp("example.com", "alice"))

    def test_old_format_preserves_description(self):
        old_data = {
            "example.com, alice, description with spaces": "secret",
        }

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.vault"
            write_main_branch_vault(path, old_data)

            manager = PwdManager.from_encrypted_file(
                str(path),
                VALID_MASTER_PASSWORD,
            )

        details = manager.get_password_and_description(
            "example.com",
            "alice",
        )
        self.assertEqual(details["password"], "secret")
        self.assertEqual(details["description"], "description with spaces")

    def test_old_format_without_description_is_rejected(self):
        old_data = {
            "example.com, alice": "secret",
        }

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.vault"
            write_main_branch_vault(path, old_data)

            with self.assertRaises(VaultFormatError):
                PwdManager.from_encrypted_file(
                    str(path),
                    VALID_MASTER_PASSWORD,
                )

    def test_old_format_with_non_string_password_is_rejected(self):
        old_data = {
            "example.com, alice, personal": 123,
        }

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.vault"
            write_main_branch_vault(path, old_data)  # type: ignore[arg-type]

            with self.assertRaises(VaultFormatError):
                PwdManager.from_encrypted_file(
                    str(path),
                    VALID_MASTER_PASSWORD,
                )


if __name__ == "__main__":
    unittest.main()
