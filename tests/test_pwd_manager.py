import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.entry import Entry
from core.keys import KEY_LEN, SALT_LEN
from core.pwd_manager import (
	DIGITS,
	LETTERS_LOWER,
	LETTERS_UPPER,
	NO_SUCH_ENTRY_MESSAGE,
	PWD_LENGTH,
	SPECIAL_CHARS,
	PwdManager,
)


class PwdManagerTests(unittest.TestCase):
	def make_manager(self) -> PwdManager:
		return PwdManager(path="vault.test", key=b"k" * KEY_LEN, salt=b"s" * SALT_LEN)

	def add_sample_entries(self, manager: PwdManager) -> None:
		manager.add_entry("github.com", "yaman", "gh-pass", "main github")
		manager.add_entry("rwth.de", "student", "rwth-pass", "university")
		manager.add_entry("github.com", "work", "work-pass", "work account")

	def test_init_stores_entries_path_key_and_salt(self):
		key = b"a" * KEY_LEN
		salt = b"b" * SALT_LEN

		manager = PwdManager("my.vault", key, salt)

		self.assertEqual(manager.entries, {})
		self.assertEqual(manager.file_path, "my.vault")
		self.assertEqual(manager._key, key)
		self.assertEqual(manager._salt, salt)

	def test_add_entry_stores_entry_and_password(self):
		manager = self.make_manager()

		manager.add_entry("github.com", "yaman", "secret", "personal")

		self.assertEqual(manager.get_entry_list_len(), 1)
		self.assertEqual(manager.get_password("github.com", "yaman"), "secret")

	def test_duplicate_entry_does_not_overwrite_password(self):
		manager = self.make_manager()
		manager.add_entry("github.com", "yaman", "old-pass", "old desc")

		with redirect_stdout(io.StringIO()):
			manager.add_entry(" GITHUB.COM ", " YAMAN ", "new-pass", "new desc")

		self.assertEqual(manager.get_entry_list_len(), 1)
		self.assertEqual(manager.get_password("github.com", "yaman"), "old-pass")

	def test_get_password_returns_message_for_missing_entry(self):
		manager = self.make_manager()

		self.assertEqual(
			manager.get_password("missing.example", "nobody"),
			NO_SUCH_ENTRY_MESSAGE,
		)

	def test_get_password_lookup_ignores_case_and_whitespace(self):
		manager = self.make_manager()
		manager.add_entry(" GitHub.com ", " Yaman ", "secret", "desc")

		self.assertEqual(manager.get_password("github.com", "yaman"), "secret")
		self.assertEqual(manager.get_password(" GITHUB.COM ", " YAMAN "), "secret")

	def test_set_password_updates_existing_entry(self):
		manager = self.make_manager()
		manager.add_entry("github.com", "yaman", "old-pass", "desc")

		manager.set_password(" GITHUB.COM ", " YAMAN ", "new-pass")

		self.assertEqual(manager.get_password("github.com", "yaman"), "new-pass")

	def test_set_password_returns_message_for_missing_entry(self):
		manager = self.make_manager()

		result = manager.set_password("missing.example", "nobody", "new-pass")

		self.assertEqual(result, NO_SUCH_ENTRY_MESSAGE)

	def test_remove_entry_by_website_and_username(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		manager.remove_entry("github.com", "yaman")

		self.assertEqual(manager.get_entry_list_len(), 2)
		self.assertEqual(manager.get_password("github.com", "yaman"), NO_SUCH_ENTRY_MESSAGE)
		self.assertEqual(manager.get_password("github.com", "work"), "work-pass")
		self.assertEqual(manager.get_password("rwth.de", "student"), "rwth-pass")

	def test_remove_entry_without_username_removes_all_matching_website_entries(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		manager.remove_entry(" github.COM ")

		self.assertEqual(manager.get_entry_list_len(), 1)
		self.assertEqual(manager.get_password("github.com", "yaman"), NO_SUCH_ENTRY_MESSAGE)
		self.assertEqual(manager.get_password("github.com", "work"), NO_SUCH_ENTRY_MESSAGE)
		self.assertEqual(manager.get_password("rwth.de", "student"), "rwth-pass")

	def test_remove_missing_entry_does_nothing(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		manager.remove_entry("missing.example", "nobody")

		self.assertEqual(manager.get_entry_list_len(), 3)

	def test_entry_exists_ignores_case_whitespace_and_description(self):
		manager = self.make_manager()
		manager.add_entry("github.com", "yaman", "secret", "original desc")

		same_entry = Entry.create_entry(" GITHUB.COM ", " YAMAN ", "different desc")

		self.assertTrue(manager.entry_exists(same_entry))

	def test_get_entry_list_returns_entries(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		entries = manager.get_entry_list()

		self.assertEqual(len(entries), 3)
		self.assertTrue(all(isinstance(entry, Entry) for entry in entries))

	def test_get_entry_by_index_returns_entry_in_insertion_order(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		first = manager.get_entry_by_index(0)
		second = manager.get_entry_by_index(1)

		self.assertEqual(first.get_website(), "github.com")
		self.assertEqual(first.get_username(), "yaman")
		self.assertEqual(second.get_website(), "rwth.de")
		self.assertEqual(second.get_username(), "student")

	def test_get_entry_by_index_rejects_negative_index(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		with self.assertRaises(IndexError):
			manager.get_entry_by_index(-1)

	def test_get_entry_by_index_rejects_too_large_index(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		with self.assertRaises(IndexError):
			manager.get_entry_by_index(3)

	def test_get_website_and_username_string_uses_entry_to_string(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		self.assertEqual(
			manager.get_website_and_username_string(),
			[
				"(github.com, yaman)",
				"(rwth.de, student)",
				"(github.com, work)",
			],
		)

	def test_get_username_and_description_returns_exact_website_matches(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		self.assertEqual(
			manager.get_username_and_description("github.com"),
			[
				("yaman", "main github"),
				("work", "work account"),
			],
		)

	def test_get_entries_by_website_returns_exact_website_matches(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		entries = manager.get_entries_by_website("github.com")

		self.assertEqual([entry.get_username() for entry in entries], ["yaman", "work"])

	def test_get_entries_by_username_returns_exact_username_matches(self):
		manager = self.make_manager()
		self.add_sample_entries(manager)

		entries = manager.get_entries_by_username("student")

		self.assertEqual(len(entries), 1)
		self.assertEqual(entries[0].get_website(), "rwth.de")

	def test_encrypt_does_nothing_for_empty_file_path(self):
		manager = self.make_manager()
		manager.file_path = ""

		with patch("core.pwd_manager.encrypt_data") as encrypt_data:
			with redirect_stdout(io.StringIO()):
				manager.encrypt()

		encrypt_data.assert_not_called()

	def test_encrypt_does_nothing_for_missing_file_path(self):
		manager = self.make_manager()
		manager.file_path = "definitely_missing_file.vault"

		with patch("core.pwd_manager.encrypt_data") as encrypt_data:
			with redirect_stdout(io.StringIO()):
				manager.encrypt()

		encrypt_data.assert_not_called()

	def test_encrypt_serializes_entries_using_current_vault_format(self):
		manager = self.make_manager()
		manager.add_entry("github.com", "yaman", "secret", "personal")

		with TemporaryDirectory() as tmp:
			path = Path(tmp) / "vault.json"
			path.touch()
			manager.file_path = str(path)

			with patch("core.pwd_manager.encrypt_data") as encrypt_data:
				manager.encrypt()

		encrypt_data.assert_called_once_with(
			data={"github.com, yaman, personal": "secret"},
			key=manager._key,
			salt=manager._salt,
			file_path=str(path),
			associated_data="",
		)

	def test_modify_master_password_updates_key_salt_and_encrypts(self):
		manager = self.make_manager()
		old_key = manager._key
		old_salt = manager._salt

		with patch.object(manager, "encrypt") as encrypt:
			manager.modify_master_password("new-master-password")

		self.assertNotEqual(manager._key, old_key)
		self.assertNotEqual(manager._salt, old_salt)
		self.assertEqual(len(manager._key), KEY_LEN)
		self.assertEqual(len(manager._salt), SALT_LEN)
		encrypt.assert_called_once()

	def test_pwd_manager_from_pwd_initializes_key_salt_and_encrypts(self):
		with TemporaryDirectory() as tmp:
			path = Path(tmp) / "vault.json"
			path.touch()

			manager = PwdManager._pwd_manager_from_pwd(str(path), "master-password")

		self.assertEqual(manager.file_path, str(path))
		self.assertEqual(len(manager._key), KEY_LEN)
		self.assertEqual(len(manager._salt), SALT_LEN)

	def test_encrypt_and_from_encrypted_file_round_trip(self):
		with TemporaryDirectory() as tmp:
			path = Path(tmp) / "vault.json"
			path.touch()

			manager = PwdManager._pwd_manager_from_pwd(str(path), "master-password")
			manager.add_entry("github.com", "yaman", "secret", "personal")
			manager.add_entry("rwth.de", "student", "rwth-pass", "university")
			manager.encrypt()

			with patch("core.pwd_manager.getpass", return_value="master-password"):
				with redirect_stdout(io.StringIO()):
					loaded = PwdManager.from_encrypted_file(str(path))

		self.assertIsInstance(loaded, PwdManager)
		self.assertEqual(loaded.get_entry_list_len(), 2)
		self.assertEqual(loaded.get_password("github.com", "yaman"), "secret")
		self.assertEqual(loaded.get_password("rwth.de", "student"), "rwth-pass")

	def test_from_encrypted_file_returns_none_for_wrong_password(self):
		with TemporaryDirectory() as tmp:
			path = Path(tmp) / "vault.json"
			path.touch()

			manager = PwdManager._pwd_manager_from_pwd(str(path), "correct-password")
			manager.add_entry("github.com", "yaman", "secret", "personal")
			manager.encrypt()

			with patch("core.pwd_manager.getpass", return_value="wrong-password"):
				with redirect_stdout(io.StringIO()):
					loaded = PwdManager.from_encrypted_file(str(path))

		self.assertIsNone(loaded)

	def test_from_encrypted_file_returns_none_for_missing_file(self):
		with patch("core.pwd_manager.getpass", return_value="master-password"):
			with redirect_stdout(io.StringIO()):
				loaded = PwdManager.from_encrypted_file("missing-file.vault")

		self.assertIsNone(loaded)

	def test_generate_pwd_has_expected_length(self):
		password = PwdManager.generate_pwd()

		self.assertEqual(len(password), PWD_LENGTH)

	def test_generate_pwd_contains_required_character_classes(self):
		password = PwdManager.generate_pwd()

		self.assertTrue(any(char in DIGITS for char in password))
		self.assertTrue(any(char in LETTERS_LOWER for char in password))
		self.assertTrue(any(char in LETTERS_UPPER for char in password))
		self.assertTrue(any(char in SPECIAL_CHARS for char in password))

	def test_pwd_satisfies_conditions_accepts_valid_password(self):
		password = "aA1!" + "x" * (PWD_LENGTH - 4)

		self.assertTrue(PwdManager._pwd_satisfies_conditions(password))

	def test_pwd_satisfies_conditions_rejects_password_without_digit(self):
		password = "aA!" + "x" * (PWD_LENGTH - 3)

		self.assertFalse(PwdManager._pwd_satisfies_conditions(password))

	def test_pwd_satisfies_conditions_rejects_password_without_lowercase(self):
		password = "A1!" + "X" * (PWD_LENGTH - 3)

		self.assertFalse(PwdManager._pwd_satisfies_conditions(password))

	def test_pwd_satisfies_conditions_rejects_password_without_uppercase(self):
		password = "a1!" + "x" * (PWD_LENGTH - 3)

		self.assertFalse(PwdManager._pwd_satisfies_conditions(password))

	def test_pwd_satisfies_conditions_rejects_password_without_special_char(self):
		password = "aA1" + "x" * (PWD_LENGTH - 3)

		self.assertFalse(PwdManager._pwd_satisfies_conditions(password))


if __name__ == "__main__":
	unittest.main()