import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.encrypt import decrypt_data, get_key_from_pwd
from core.entry import Entry
from core.pwd_manager import (
    NO_SUCH_ENTRY_MESSAGE,
    NO_SUCH_TOTP_MESSAGE,
    PWD,
    PWD_LENGTH,
    TOTP_SECRET,
    TOTP_URI,
    URI_INVALID_MESSAGE,
    PwdManager,
)
from tests.helpers import (
    NEW_MASTER_PASSWORD,
    SECOND_VALID_SECRET,
    SECOND_VALID_URI,
    VALID_MASTER_PASSWORD,
    VALID_SECRET,
    VALID_URI,
    write_new_format_vault,
)


class PwdManagerEntryTests(unittest.TestCase):
    def setUp(self):
        self.manager = PwdManager()
        self.manager.add_entry("example.com", "alice", "secret", "personal")

    def test_add_and_get_password(self):
        self.assertEqual(self.manager.get_password("example.com", "alice"), "secret")

    def test_lookup_is_case_and_whitespace_insensitive(self):
        self.assertEqual(self.manager.get_password(" Example.COM ", " ALICE "), "secret")

    def test_duplicate_entry_is_not_added(self):
        self.manager.add_entry(" EXAMPLE.COM ", "Alice", "different", "other")
        self.assertEqual(self.manager.get_entry_list_len(), 1)
        self.assertEqual(self.manager.get_password("example.com", "alice"), "secret")

    def test_missing_entry_returns_message(self):
        self.assertEqual(self.manager.get_password("missing", "alice"), NO_SUCH_ENTRY_MESSAGE)

    def test_set_password_updates_existing_entry(self):
        self.assertIsNone(self.manager.set_password("example.com", "alice", "new-secret"))
        self.assertEqual(self.manager.get_password("example.com", "alice"), "new-secret")

    def test_set_password_for_missing_entry_returns_message(self):
        self.assertEqual(
            self.manager.set_password("missing", "alice", "new-secret"),
            NO_SUCH_ENTRY_MESSAGE,
        )

    def test_remove_specific_entry(self):
        self.manager.remove_entry("example.com", "alice")
        self.assertEqual(self.manager.get_entry_list_len(), 0)

    def test_remove_missing_entry_is_noop(self):
        self.manager.remove_entry("missing", "alice")
        self.assertEqual(self.manager.get_entry_list_len(), 1)

    def test_remove_all_entries_for_website_is_case_insensitive(self):
        self.manager.add_entry("example.com", "bob", "two", "")
        self.manager.add_entry("other.com", "alice", "three", "")
        self.manager.remove_entry(" EXAMPLE.COM ")
        self.assertEqual(self.manager.get_entry_list_len(), 1)
        self.assertEqual(self.manager.get_password("other.com", "alice"), "three")

    def test_get_entry_by_index(self):
        self.assertTrue(
            self.manager.get_entry_by_index(0).is_equal(
                Entry.create_entry("example.com", "alice")
            )
        )

    def test_get_entry_by_index_rejects_invalid_indices(self):
        with self.assertRaises(IndexError):
            self.manager.get_entry_by_index(-1)
        with self.assertRaises(IndexError):
            self.manager.get_entry_by_index(1)

    def test_listing_helpers(self):
        self.manager.add_entry("example.com", "bob", "two", "work")
        self.assertEqual(
            self.manager.get_username_and_description("example.com"),
            [("alice", "personal"), ("bob", "work")],
        )
        self.assertEqual(
            self.manager.get_website_and_username_string(),
            ["(example.com, alice)", "(example.com, bob)"],
        )
        self.assertEqual(len(self.manager.get_entries_by_website("example.com")), 2)
        self.assertEqual(len(self.manager.get_entries_by_username("alice")), 1)


class PasswordGenerationTests(unittest.TestCase):
    def test_generated_password_meets_all_requirements(self):
        password = PwdManager.generate_pwd()
        self.assertEqual(len(password), PWD_LENGTH)
        self.assertEqual(PwdManager._pwd_satisfies_conditions(password), (True, ""))

    def test_password_requirement_reasons(self):
        cases = [
            ("Aa1!", "len"),
            ("Abcdefgh!", "digit"),
            ("ABCDEFG1!", "lower"),
            ("abcdefg1!", "upper"),
            ("Abcdefg1", "special"),
        ]
        for password, reason in cases:
            with self.subTest(password=password):
                self.assertEqual(
                    PwdManager._pwd_satisfies_conditions(password, len_min=8),
                    (False, reason),
                )


class PwdManagerTOTPTests(unittest.TestCase):
    def setUp(self):
        self.manager = PwdManager()
        self.manager.add_entry("example.com", "alice", "secret", "")

    def test_set_valid_totp_config(self):
        self.assertIsNone(self.manager.set_totp_config("example.com", "alice", VALID_URI))
        self.assertTrue(self.manager.has_totp("example.com", "alice"))
        entry = self.manager.get_entry_by_index(0)
        self.assertEqual(entry.get_totp_config().issuer, "ACME Co")  # type: ignore[union-attr]
        self.assertEqual(self.manager.entries[entry][TOTP_SECRET], VALID_SECRET)
        self.assertEqual(self.manager.entries[entry][TOTP_URI], VALID_URI)

    def test_setting_totp_again_replaces_uri_secret_and_config(self):
        self.manager.set_totp_config("example.com", "alice", VALID_URI)
        self.manager.set_totp_config("example.com", "alice", SECOND_VALID_URI)
        entry = self.manager.get_entry_by_index(0)
        self.assertEqual(self.manager.entries[entry][TOTP_SECRET], SECOND_VALID_SECRET)
        self.assertEqual(self.manager.entries[entry][TOTP_URI], SECOND_VALID_URI)
        self.assertEqual(entry.get_totp_config().issuer, "Other Issuer")  # type: ignore[union-attr]

    def test_set_totp_for_missing_entry(self):
        self.assertEqual(
            self.manager.set_totp_config("missing", "alice", VALID_URI),
            NO_SUCH_ENTRY_MESSAGE,
        )

    def test_rejects_invalid_totp_uri_without_modifying_entry(self):
        self.assertEqual(
            self.manager.set_totp_config("example.com", "alice", "not-a-uri"),
            URI_INVALID_MESSAGE,
        )
        entry = self.manager.get_entry_by_index(0)
        self.assertFalse(self.manager.has_totp("example.com", "alice"))
        self.assertEqual(self.manager.entries[entry][TOTP_SECRET], "")
        self.assertEqual(self.manager.entries[entry][TOTP_URI], "")
        self.assertIsNone(entry.get_totp_config())

    def test_invalid_replacement_does_not_remove_existing_totp(self):
        self.manager.set_totp_config("example.com", "alice", VALID_URI)
        self.assertEqual(
            self.manager.set_totp_config("example.com", "alice", "not-a-uri"),
            URI_INVALID_MESSAGE,
        )
        entry = self.manager.get_entry_by_index(0)
        self.assertEqual(self.manager.entries[entry][TOTP_URI], VALID_URI)
        self.assertEqual(self.manager.entries[entry][TOTP_SECRET], VALID_SECRET)

    def test_get_totp_for_missing_entry(self):
        self.assertEqual(self.manager.get_totp("missing", "alice"), NO_SUCH_ENTRY_MESSAGE)

    def test_get_totp_without_config(self):
        self.assertEqual(
            self.manager.get_totp("example.com", "alice"),
            NO_SUCH_TOTP_MESSAGE,
        )

    @patch(
        "core.pwd_manager.TOTP_Config.seconds_remaining",
        return_value=9,
    )
    @patch("core.pwd_manager.TOTP")
    def test_get_totp_uses_stored_secret_and_config(
        self,
        totp_class: Mock,
        seconds_remaining: Mock,
    ):
        self.manager.set_totp_config("example.com", "alice", VALID_URI)
        totp_class.return_value.now.return_value = "123456"

        self.assertEqual(
            self.manager.get_totp("example.com", "alice"),
            "Code: 123456. Valid for 9 seconds.",
        )

        totp_class.assert_called_once()
        kwargs = totp_class.call_args.kwargs
        self.assertEqual(kwargs["s"], VALID_SECRET)
        self.assertEqual(kwargs["digits"], 6)
        self.assertEqual(kwargs["interval"], 30)
        seconds_remaining.assert_called_once()


class FormatValidationTests(unittest.TestCase):
    def test_detects_old_format(self):
        old = {"site, user, description": "password"}
        self.assertTrue(PwdManager._has_old_format(old))
        self.assertFalse(PwdManager._has_new_format(old))

    def test_detects_password_only_new_format(self):
        new = {"site, user, description": {PWD: "password", TOTP_URI: ""}}
        self.assertTrue(PwdManager._has_new_format(new))
        self.assertFalse(PwdManager._has_old_format(new))

    def test_detects_totp_new_format(self):
        new = {"site, user, description": {PWD: "password", TOTP_URI: VALID_URI}}
        self.assertTrue(PwdManager._has_new_format(new))

    def test_new_format_requires_password_and_totp_uri(self):
        self.assertFalse(
            PwdManager._has_new_format({"site, user, description": {PWD: "password"}})
        )
        self.assertFalse(
            PwdManager._has_new_format({"site, user, description": {TOTP_URI: ""}})
        )

    def test_new_format_rejects_non_string_values(self):
        self.assertFalse(
            PwdManager._has_new_format(
                {"site, user, description": {PWD: 123, TOTP_URI: ""}}
            )
        )
        self.assertFalse(
            PwdManager._has_new_format(
                {"site, user, description": {PWD: "password", TOTP_URI: None}}
            )
        )

    def test_rejects_mixed_format(self):
        mixed = {
            "one, user, desc": "password",
            "two, user, desc": {PWD: "password", TOTP_URI: ""},
        }
        self.assertFalse(PwdManager._has_old_format(mixed))
        self.assertFalse(PwdManager._has_new_format(mixed))

    def test_rejects_malformed_entry_key(self):
        self.assertFalse(PwdManager._has_old_format({"site,user": "password"}))
        self.assertFalse(
            PwdManager._has_new_format(
                {"site,user": {PWD: "password", TOTP_URI: ""}}
            )
        )

    def test_empty_vault_is_a_valid_new_format(self):
        self.assertTrue(PwdManager._has_new_format({}))


class PwdManagerPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "vault.json"
        self.path.touch()

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_manager(self):
        return PwdManager.pwd_manager_from_pwd(str(self.path), VALID_MASTER_PASSWORD)

    def test_password_entries_survive_save_and_reload(self):
        manager = self.create_manager()
        manager.add_entry("example.com", "alice", "secret", "personal")
        manager.add_entry("other.com", "bob", "second", "work")
        manager.encrypt()
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.get_password("example.com", "alice"), "secret")  # type: ignore[union-attr]
        self.assertEqual(restored.get_password("other.com", "bob"), "second")  # type: ignore[union-attr]
        self.assertFalse(restored.has_totp("example.com", "alice"))  # type: ignore[union-attr]

    def test_password_only_entry_is_saved_with_empty_totp_uri(self):
        manager = self.create_manager()
        manager.add_entry("example.com", "alice", "secret", "personal")
        manager.encrypt()
        _, key = get_key_from_pwd(VALID_MASTER_PASSWORD, str(self.path))
        self.assertEqual(
            decrypt_data(key, str(self.path)),
            {
                "example.com, alice, personal": {
                    PWD: "secret",
                    TOTP_URI: "",
                }
            },
        )

    def test_wrong_master_password_does_not_open_vault(self):
        manager = self.create_manager()
        manager.add_entry("example.com", "alice", "secret", "")
        manager.encrypt()
        self.assertIsNone(PwdManager.from_encrypted_file(str(self.path), NEW_MASTER_PASSWORD))

    def test_master_password_change_reencrypts_vault(self):
        manager = self.create_manager()
        manager.add_entry("example.com", "alice", "secret", "")
        manager.encrypt()
        manager.modify_master_password(NEW_MASTER_PASSWORD)
        self.assertIsNone(PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD))
        restored = PwdManager.from_encrypted_file(str(self.path), NEW_MASTER_PASSWORD)
        self.assertEqual(restored.get_password("example.com", "alice"), "secret")  # type: ignore[union-attr]

    def test_empty_new_vault_can_be_reopened(self):
        self.create_manager()
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.get_entry_list_len(), 0)  # type: ignore[union-attr]

    def test_totp_uri_reconstructs_config_and_secret_after_reload(self):
        manager = self.create_manager()
        manager.add_entry("example.com", "alice", "secret", "")
        manager.set_totp_config("example.com", "alice", VALID_URI)
        manager.encrypt()
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(restored)
        self.assertTrue(restored.has_totp("example.com", "alice"))  # type: ignore[union-attr]
        restored_entry = restored.get_entry_by_index(0)  # type: ignore[union-attr]
        self.assertEqual(restored.entries[restored_entry][TOTP_SECRET], VALID_SECRET)  # type: ignore[union-attr]
        self.assertEqual(restored.entries[restored_entry][TOTP_URI], VALID_URI)  # type: ignore[union-attr]
        self.assertEqual(restored_entry.get_totp_config().issuer, "ACME Co")  # type: ignore[union-attr]

    def test_saved_new_format_contains_uri_not_duplicated_secret(self):
        manager = self.create_manager()
        manager.add_entry("example.com", "alice", "secret", "")
        manager.set_totp_config("example.com", "alice", VALID_URI)
        manager.encrypt()
        salt, key = get_key_from_pwd(VALID_MASTER_PASSWORD, str(self.path))
        self.assertEqual(salt, manager._salt)
        value = next(iter(decrypt_data(key, str(self.path)).values()))
        self.assertEqual(value, {PWD: "secret", TOTP_URI: VALID_URI})
        self.assertNotIn(TOTP_SECRET, value)

    def test_mixed_totp_and_password_only_entries_survive_reload(self):
        manager = self.create_manager()
        manager.add_entry("totp.com", "alice", "one", "")
        manager.set_totp_config("totp.com", "alice", VALID_URI)
        manager.add_entry("plain.com", "bob", "two", "")
        manager.encrypt()
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertTrue(restored.has_totp("totp.com", "alice"))  # type: ignore[union-attr]
        self.assertFalse(restored.has_totp("plain.com", "bob"))  # type: ignore[union-attr]
        self.assertEqual(restored.get_password("plain.com", "bob"), "two")  # type: ignore[union-attr]

    def test_loaded_password_only_vault_can_be_saved_again(self):
        write_new_format_vault(
            self.path,
            {
                "example.com, alice, note": {
                    PWD: "secret",
                    TOTP_URI: "",
                }
            },
        )
        restored = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertIsNotNone(restored)
        restored.encrypt()  # type: ignore[union-attr]
        reopened = PwdManager.from_encrypted_file(str(self.path), VALID_MASTER_PASSWORD)
        self.assertEqual(reopened.get_password("example.com", "alice"), "secret")  # type: ignore[union-attr]

