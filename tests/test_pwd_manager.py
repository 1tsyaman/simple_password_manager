import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.entry import Entry
from core.errors import (
    CorruptedVaultError,
    EntryExistsError,
    EntryHasNoTotp,
    NoSuchEntryError,
    PasswordError,
    PasswordRequirementsError,
    TotpUriError,
    VaultFormatError,
)
from core.keys import KEY_LEN, SALT_LEN
from core.pwd_manager import (
    DIGITS,
    LETTERS_LOWER,
    LETTERS_UPPER,
    PWD,
    PWD_LENGTH,
    SPECIAL_CHARS,
    TOTP_URI,
    PwdManager,
)


VALID_MASTER_PASSWORD = "Master1!"
VALID_TOTP_URI = (
    "otpauth://totp/Example:alice?"
    "secret=JBSWY3DPEHPK3PXP&issuer=Example&algorithm=SHA1&digits=6&period=30"
)


class PwdManagerTests(unittest.TestCase):
    def make_manager(self) -> PwdManager:
        return PwdManager(
            path="vault.test",
            key=b"k" * KEY_LEN,
            salt=b"s" * SALT_LEN,
        )

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

    def test_duplicate_entry_raises_and_does_not_overwrite(self):
        manager = self.make_manager()
        manager.add_entry("github.com", "yaman", "old-pass", "old desc")

        with self.assertRaises(EntryExistsError):
            manager.add_entry(" GITHUB.COM ", " YAMAN ", "new-pass", "new desc")

        self.assertEqual(manager.get_entry_list_len(), 1)
        self.assertEqual(manager.get_password("github.com", "yaman"), "old-pass")

    def test_get_password_raises_for_missing_entry(self):
        manager = self.make_manager()

        with self.assertRaises(NoSuchEntryError):
            manager.get_password("missing.example", "nobody")

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

    def test_set_password_raises_for_missing_entry(self):
        manager = self.make_manager()

        with self.assertRaises(NoSuchEntryError):
            manager.set_password("missing.example", "nobody", "new-pass")

    def test_update_entry_updates_all_mutable_fields(self):
        manager = self.make_manager()
        manager.add_entry("old.com", "old-user", "old-pass", "old-desc")

        manager.update_entry(
            "old.com",
            "old-user",
            "new.com",
            "new-user",
            "new-pass",
            "new-desc",
        )

        self.assertEqual(manager.get_password("new.com", "new-user"), "new-pass")
        details = manager.get_password_and_description("new.com", "new-user")
        self.assertEqual(details["description"], "new-desc")

        with self.assertRaises(NoSuchEntryError):
            manager.get_password("old.com", "old-user")

    def test_update_entry_raises_for_missing_entry(self):
        manager = self.make_manager()

        with self.assertRaises(NoSuchEntryError):
            manager.update_entry(
                "missing",
                "nobody",
                "new",
                "new",
                "new-pass",
                "new-desc",
            )

    def test_remove_entry_by_website_and_username(self):
        manager = self.make_manager()
        self.add_sample_entries(manager)

        manager.remove_entry("github.com", "yaman")

        self.assertEqual(manager.get_entry_list_len(), 2)
        with self.assertRaises(NoSuchEntryError):
            manager.get_password("github.com", "yaman")
        self.assertEqual(manager.get_password("github.com", "work"), "work-pass")
        self.assertEqual(manager.get_password("rwth.de", "student"), "rwth-pass")

    def test_remove_missing_entry_is_noop(self):
        manager = self.make_manager()
        self.add_sample_entries(manager)

        manager.remove_entry("missing.example", "nobody")

        self.assertEqual(manager.get_entry_list_len(), 3)

    def test_entry_exists_ignores_case_whitespace_and_description(self):
        manager = self.make_manager()
        manager.add_entry("github.com", "yaman", "secret", "original desc")

        same_entry = Entry.create_entry(" GITHUB.COM ", " YAMAN ", "different desc")

        self.assertTrue(manager.entry_exists(same_entry))

    def test_entry_list_and_lookup_helpers(self):
        manager = self.make_manager()
        self.add_sample_entries(manager)

        self.assertEqual(manager.get_entry_list_len(), 3)
        self.assertEqual(
            manager.get_website_and_username_string_list(),
            [
                "(github.com, yaman)",
                "(rwth.de, student)",
                "(github.com, work)",
            ],
        )
        self.assertEqual(
            manager.get_website_username_pair_list(),
            [
                ("github.com", "yaman"),
                ("rwth.de", "student"),
                ("github.com", "work"),
            ],
        )

        self.assertEqual(
            [entry.get_username() for entry in manager.get_entries_by_website("github.com")],
            ["yaman", "work"],
        )
        self.assertEqual(
            [entry.get_website() for entry in manager.get_entries_by_username("student")],
            ["rwth.de"],
        )

    def test_get_entry_by_index_raises_for_out_of_range_index(self):
        manager = self.make_manager()
        self.add_sample_entries(manager)

        with self.assertRaises(IndexError):
            manager.get_entry_by_index(3)

    def test_get_password_and_description_raises_for_missing_entry(self):
        manager = self.make_manager()

        with self.assertRaises(NoSuchEntryError):
            manager.get_password_and_description("missing", "nobody")

    def test_totp_configuration_and_generation(self):
        manager = self.make_manager()
        manager.add_entry("example.com", "alice", "secret", "desc")

        self.assertFalse(manager.has_totp("example.com", "alice"))

        manager.set_totp_config("example.com", "alice", VALID_TOTP_URI)

        self.assertTrue(manager.has_totp("example.com", "alice"))
        code, remaining = manager.get_totp("example.com", "alice")
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.assertGreaterEqual(remaining, 1)
        self.assertLessEqual(remaining, 30)

    def test_get_totp_raises_for_missing_entry_or_config(self):
        manager = self.make_manager()

        with self.assertRaises(NoSuchEntryError):
            manager.get_totp("missing", "nobody")

        manager.add_entry("example.com", "alice", "secret", "")
        with self.assertRaises(EntryHasNoTotp):
            manager.get_totp("example.com", "alice")

    def test_set_totp_config_raises_for_missing_entry_or_bad_uri(self):
        manager = self.make_manager()

        with self.assertRaises(NoSuchEntryError):
            manager.set_totp_config("missing", "nobody", VALID_TOTP_URI)

        manager.add_entry("example.com", "alice", "secret", "")
        with self.assertRaises(TotpUriError):
            manager.set_totp_config("example.com", "alice", "not-a-totp-uri")

    def test_encrypt_serializes_current_vault_format(self):
        manager = self.make_manager()
        manager.add_entry("github.com", "yaman", "secret", "personal")

        with patch("core.pwd_manager.encrypt_data") as encrypt_data:
            manager.encrypt()

        encrypt_data.assert_called_once_with(
            data={
                "github.com, yaman, personal": {
                    PWD: "secret",
                    TOTP_URI: "",
                },
            },
            key=manager._key,
            salt=manager._salt,
            file_path=manager.file_path,
            associated_data="",
        )

    def test_encrypt_propagates_missing_file_error(self):
        manager = self.make_manager()
        manager.file_path = "definitely_missing_file.vault"

        with self.assertRaises(FileNotFoundError):
            manager.encrypt()

    def test_snapshot_is_independent_copy(self):
        manager = self.make_manager()
        manager.add_entry("example.com", "alice", "old-pass", "desc")

        snapshot = manager.get_snapshot()
        snapshot.set_password("example.com", "alice", "new-pass")

        self.assertEqual(manager.get_password("example.com", "alice"), "old-pass")
        self.assertEqual(snapshot.get_password("example.com", "alice"), "new-pass")

    def test_modify_master_password_updates_key_and_salt(self):
        manager = self.make_manager()
        new_salt = b"n" * SALT_LEN
        new_key = b"x" * KEY_LEN

        with patch("core.pwd_manager.derive_key", return_value=(new_salt, new_key)):
            with patch.object(manager, "encrypt") as encrypt:
                manager.modify_master_password(VALID_MASTER_PASSWORD)

        self.assertEqual(manager._salt, new_salt)
        self.assertEqual(manager._key, new_key)
        encrypt.assert_called_once_with()

    def test_modify_master_password_rejects_weak_password(self):
        manager = self.make_manager()

        with self.assertRaises(PasswordRequirementsError) as ctx:
            manager.modify_master_password("weak")

        self.assertTrue(ctx.exception.reason)

    def test_modify_master_password_rolls_back_when_encrypt_fails(self):
        manager = self.make_manager()
        old_key = manager._key
        old_salt = manager._salt

        with patch(
            "core.pwd_manager.derive_key",
            return_value=(b"n" * SALT_LEN, b"x" * KEY_LEN),
        ):
            with patch.object(manager, "encrypt", side_effect=OSError("write failed")):
                with self.assertRaises(OSError):
                    manager.modify_master_password(VALID_MASTER_PASSWORD)

        self.assertEqual(manager._key, old_key)
        self.assertEqual(manager._salt, old_salt)

    def test_pwd_manager_from_pwd_rejects_weak_password(self):
        with self.assertRaises(PasswordRequirementsError):
            PwdManager.pwd_manager_from_pwd("vault.vault", "weak")

    def test_pwd_manager_from_pwd_initializes_and_encrypts(self):
        salt = b"s" * SALT_LEN
        key = b"k" * KEY_LEN

        with patch("core.pwd_manager.derive_key", return_value=(salt, key)):
            with patch.object(PwdManager, "encrypt") as encrypt:
                manager = PwdManager.pwd_manager_from_pwd(
                    "vault.vault",
                    VALID_MASTER_PASSWORD,
                )

        self.assertEqual(manager.file_path, "vault.vault")
        self.assertEqual(manager._salt, salt)
        self.assertEqual(manager._key, key)
        encrypt.assert_called_once_with()

    def test_encrypt_and_from_encrypted_file_round_trip(self):
        key = b"k" * KEY_LEN
        salt = b"s" * SALT_LEN

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()

            manager = PwdManager(str(path), key, salt)
            manager.add_entry("github.com", "yaman", "secret", "personal")
            manager.add_entry("example.com", "alice", "other-secret", "totp")
            manager.set_totp_config("example.com", "alice", VALID_TOTP_URI)
            manager.encrypt()

            with patch("core.encrypt.derive_key", return_value=(salt, key)):
                loaded = PwdManager.from_encrypted_file(
                    str(path),
                    VALID_MASTER_PASSWORD,
                )

        self.assertEqual(loaded.get_entry_list_len(), 2)
        self.assertEqual(loaded.get_password("github.com", "yaman"), "secret")
        self.assertEqual(
            loaded.get_password("example.com", "alice"),
            "other-secret",
        )
        self.assertTrue(loaded.has_totp("example.com", "alice"))

    def test_from_encrypted_file_raises_corrupted_vault_for_wrong_key(self):
        key = b"k" * KEY_LEN
        salt = b"s" * SALT_LEN

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()

            manager = PwdManager(str(path), key, salt)
            manager.encrypt()

            with patch(
                "core.encrypt.derive_key",
                return_value=(salt, b"x" * KEY_LEN),
            ):
                with self.assertRaises(CorruptedVaultError):
                    PwdManager.from_encrypted_file(
                        str(path),
                        VALID_MASTER_PASSWORD,
                    )

    def test_from_encrypted_file_raises_for_missing_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.vault"

            with self.assertRaises(FileNotFoundError):
                PwdManager.from_encrypted_file(
                    str(path),
                    VALID_MASTER_PASSWORD,
                )

    def test_from_encrypted_file_rejects_weak_password_before_loading(self):
        with self.assertRaises(PasswordError):
            PwdManager.from_encrypted_file("missing.vault", "weak")

    def test_from_encrypted_file_rejects_unknown_decrypted_format(self):
        with patch(
            "core.pwd_manager.PwdManager._pwd_satisfies_conditions",
            return_value=(True, ""),
        ):
            with patch(
                "core.pwd_manager.get_key_from_pwd",
                return_value=(b"s" * SALT_LEN, b"k" * KEY_LEN),
            ):
                with patch(
                    "core.pwd_manager.decrypt_data",
                    return_value={"invalid": object()},
                ):
                    with self.assertRaises(VaultFormatError):
                        PwdManager.from_encrypted_file(
                            "vault.vault",
                            VALID_MASTER_PASSWORD,
                        )

    def test_generate_random_pwd_has_expected_length_and_classes(self):
        password = PwdManager.generate_random_pwd()

        self.assertEqual(len(password), PWD_LENGTH)
        self.assertTrue(any(char in DIGITS for char in password))
        self.assertTrue(any(char in LETTERS_LOWER for char in password))
        self.assertTrue(any(char in LETTERS_UPPER for char in password))
        self.assertTrue(any(char in SPECIAL_CHARS for char in password))

    def test_pwd_satisfies_conditions_returns_boolean_and_reason(self):
        valid = "Aa1!" + "x" * (PWD_LENGTH - 4)
        satisfies, reason = PwdManager._pwd_satisfies_conditions(valid)
        self.assertTrue(satisfies)
        self.assertEqual(reason, "")

        cases = [
            ("Aa1!", "must be at least"),
            ("A1!" + "X" * (PWD_LENGTH - 3), "lowercase"),
            ("a1!" + "x" * (PWD_LENGTH - 3), "uppercase"),
            ("Aa!" + "x" * (PWD_LENGTH - 3), "digit"),
            ("Aa1" + "x" * (PWD_LENGTH - 3), "special"),
        ]

        for password, expected_reason in cases:
            with self.subTest(password=password):
                satisfies, reason = PwdManager._pwd_satisfies_conditions(password)
                self.assertFalse(satisfies)
                self.assertIn(expected_reason, reason)


if __name__ == "__main__":
    unittest.main()
