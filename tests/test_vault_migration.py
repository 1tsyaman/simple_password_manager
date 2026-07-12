import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.encrypt import decrypt_data, get_key_from_pwd
from core.pwd_manager import PWD, TOTP_SECRET, TOTP_URI, PwdManager
from tests.helpers import VALID_MASTER_PASSWORD, write_main_branch_vault


class MainBranchVaultMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "legacy.vault"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_loads_all_entries_from_main_branch_format(self, _sleep):
        write_main_branch_vault(
            self.path,
            {
                "example.com, alice, personal": "secret-one",
                "other.com, bob, work": "secret-two",
            },
        )
        manager = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.get_entry_list_len(), 2)  # type: ignore[union-attr]
        self.assertEqual(manager.get_password("example.com", "alice"), "secret-one")  # type: ignore[union-attr]
        self.assertEqual(manager.get_password("other.com", "bob"), "secret-two")  # type: ignore[union-attr]

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_preserves_description_containing_commas(self, _sleep):
        write_main_branch_vault(
            self.path,
            {"example.com, alice, personal, banking account": "secret"},
        )
        manager = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        entry = manager.get_entry_by_index(0)  # type: ignore[union-attr]
        self.assertEqual(entry.get_description(), "personal, banking account")

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_saving_loaded_main_vault_converts_to_uri_format(self, _sleep):
        write_main_branch_vault(self.path, {"example.com, alice, note": "secret"})
        manager = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        manager.encrypt()  # type: ignore[union-attr]

        _, key = get_key_from_pwd(VALID_MASTER_PASSWORD, str(self.path))
        converted = decrypt_data(key, str(self.path))
        self.assertTrue(PwdManager._has_new_format(converted))
        self.assertEqual(
            converted,
            {
                "example.com, alice, note": {
                    PWD: "secret",
                    TOTP_URI: "",
                }
            },
        )

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_converted_main_vault_can_be_reopened_and_saved_again(self, _sleep):
        write_main_branch_vault(self.path, {"example.com, alice, note": "secret"})
        manager = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        manager.encrypt()  # type: ignore[union-attr]
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        restored.encrypt()  # type: ignore[union-attr]
        reopened = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(reopened)
        self.assertEqual(reopened.get_password("example.com", "alice"), "secret")  # type: ignore[union-attr]

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_conversion_does_not_invent_totp_data(self, _sleep):
        write_main_branch_vault(self.path, {"example.com, alice, note": "secret"})
        manager = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertFalse(manager.has_totp("example.com", "alice"))  # type: ignore[union-attr]
        manager.encrypt()  # type: ignore[union-attr]
        _, key = get_key_from_pwd(VALID_MASTER_PASSWORD, str(self.path))
        value = next(iter(decrypt_data(key, str(self.path)).values()))
        self.assertEqual(value[TOTP_URI], "")
        self.assertNotIn(TOTP_SECRET, value)

    @patch("core.pwd_manager.sleep", return_value=None)
    def test_empty_main_branch_vault_is_loaded_and_converted(self, _sleep):
        write_main_branch_vault(self.path, {})
        manager = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(manager)
        self.assertEqual(manager.get_entry_list_len(), 0)  # type: ignore[union-attr]
        manager.encrypt()  # type: ignore[union-attr]
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.get_entry_list_len(), 0)  # type: ignore[union-attr]

    def test_malformed_main_branch_data_is_rejected(self):
        write_main_branch_vault(self.path, {"missing separators": "secret"})
        self.assertIsNone(PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD))

    def test_mixed_old_and_new_data_is_rejected(self):
        write_main_branch_vault(
            self.path,
            {
                "old.com, user, note": "secret",
                "new.com, user, note": {PWD: "secret", TOTP_URI: ""},  # type: ignore[dict-item]
            },
        )
        self.assertIsNone(PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD))
