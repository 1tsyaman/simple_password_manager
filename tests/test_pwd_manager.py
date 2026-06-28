import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pwd_manager import DIGITS, LETTERS, PWD_LENGTH, SPECIAL_CHARS, PwdManager


class PwdManagerEntryTests(unittest.TestCase):
    def test_add_and_get_password(self):
        manager = PwdManager()

        manager.add_entry("github.com", "yaman", "secret", "main account")

        self.assertEqual(manager.get_password("github.com", "yaman"), "secret")

    def test_get_password_matches_case_and_whitespace_insensitively(self):
        manager = PwdManager()

        manager.add_entry(" GitHub.COM ", " Yaman ", "secret", "main account")

        self.assertEqual(manager.get_password("github.com", "yaman"), "secret")

    def test_get_password_returns_message_for_missing_entry(self):
        manager = PwdManager()

        self.assertEqual(manager.get_password("missing.example", "nobody"), "No such entry.")

    def test_duplicate_entry_does_not_override_existing_password(self):
        manager = PwdManager()

        manager.add_entry("github.com", "yaman", "first", "old")
        manager.add_entry(" GitHub.COM ", " Yaman ", "second", "new")

        self.assertEqual(manager.get_password("github.com", "yaman"), "first")
        self.assertEqual(len(manager.entries), 1)

    def test_remove_single_entry_by_website_and_username(self):
        manager = PwdManager()
        manager.add_entry("github.com", "yaman", "secret", "main account")
        manager.add_entry("github.com", "other", "other-secret", "other account")

        manager.remove_entry("github.com", "yaman")

        self.assertEqual(manager.get_password("github.com", "yaman"), "No such entry.")
        self.assertEqual(manager.get_password("github.com", "other"), "other-secret")

    def test_remove_website_entries_removes_all_matching_website_entries(self):
        manager = PwdManager()
        manager.add_entry("github.com", "yaman", "secret", "main account")
        manager.add_entry(" GitHub.COM ", "other", "other-secret", "other account")
        manager.add_entry("example.org", "yaman", "keep-me", "other site")

        manager.remove_entry("github.com")

        self.assertEqual(manager.get_password("github.com", "yaman"), "No such entry.")
        self.assertEqual(manager.get_password("github.com", "other"), "No such entry.")
        self.assertEqual(manager.get_password("example.org", "yaman"), "keep-me")

    def test_encrypt_and_exit_serializes_entries_before_encrypting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault.json"
            vault_path.touch()

            manager = PwdManager(str(vault_path), key=b"k" * 32, salt=b"s" * 16)
            manager.add_entry("github.com", "yaman", "secret", "main account")

            with patch("pwd_manager.encrypt_data") as encrypt_data:
                manager.encrypt_and_exit()

            encrypt_data.assert_called_once_with(
                data={"github.com, yaman, main account": "secret"},
                key=b"k" * 32,
                salt=b"s" * 16,
                file_path=str(vault_path),
                associated_data="",
            )

    def test_from_encrypted_file_loads_decrypted_entries(self):
        decrypted_data = {
            "github.com, yaman, main account": "secret",
            "example.org, alice, description, with comma": "another-secret",
        }

        with patch("pwd_manager.getpass", return_value="master-password"), \
             patch("pwd_manager.get_key_from_pwd", return_value=(b"s" * 16, b"k" * 32)), \
             patch("pwd_manager.decrypt_data", return_value=decrypted_data):
            manager = PwdManager.from_encrypted_file("vault.json")

        self.assertIsNotNone(manager)
        self.assertEqual(manager.get_password("github.com", "yaman"), "secret")
        self.assertEqual(manager.get_password("example.org", "alice"), "another-secret")


class PwdManagerPasswordGenerationTests(unittest.TestCase):
    def test_generate_pwd_has_expected_length_and_allowed_characters(self):
        password = PwdManager.generate_pwd()
        allowed_chars = set(LETTERS + DIGITS + SPECIAL_CHARS)

        self.assertEqual(len(password), PWD_LENGTH)
        self.assertTrue(set(password).issubset(allowed_chars))


if __name__ == "__main__":
    unittest.main()
