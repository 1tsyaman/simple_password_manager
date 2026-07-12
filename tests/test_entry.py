import unittest

from core.entry import Entry
from core.totp import TOTP_Config


class EntryTests(unittest.TestCase):
    def test_create_entry_sets_fields(self):
        entry = Entry.create_entry("example.com", "alice", "personal")
        self.assertEqual(entry.get_website(), "example.com")
        self.assertEqual(entry.get_username(), "alice")
        self.assertEqual(entry.get_description(), "personal")
        self.assertIsNone(entry.get_totp_config())

    def test_create_entry_accepts_totp_config(self):
        config = TOTP_Config("issuer", "account")
        entry = Entry.create_entry("example.com", "alice", "personal", config)
        self.assertIs(entry.get_totp_config(), config)

    def test_setters_update_fields(self):
        entry = Entry()
        config = TOTP_Config("issuer", "account")
        entry.set_website("example.com")
        entry.set_username("alice")
        entry.set_description("note")
        entry.set_totp_config(config)
        self.assertEqual(entry.get_website(), "example.com")
        self.assertEqual(entry.get_username(), "alice")
        self.assertEqual(entry.get_description(), "note")
        self.assertIs(entry.get_totp_config(), config)

    def test_totp_config_can_be_cleared(self):
        entry = Entry.create_entry("example.com", "alice", totp_config=TOTP_Config("issuer", "account"))
        entry.set_totp_config(None)
        self.assertIsNone(entry.get_totp_config())

    def test_equality_is_case_and_whitespace_insensitive(self):
        left = Entry.create_entry(" Example.COM ", " Alice ", "one")
        right = Entry.create_entry("example.com", "alice", "two")
        self.assertTrue(left.is_equal(right))

    def test_equality_ignores_description_and_totp_config(self):
        left = Entry.create_entry("example.com", "alice", "one", TOTP_Config("one", "one"))
        right = Entry.create_entry("example.com", "alice", "two", TOTP_Config("two", "two"))
        self.assertTrue(left.is_equal(right))

    def test_equality_uses_both_website_and_username(self):
        base = Entry.create_entry("example.com", "alice")
        self.assertFalse(base.is_equal(Entry.create_entry("other.com", "alice")))
        self.assertFalse(base.is_equal(Entry.create_entry("example.com", "bob")))

    def test_to_string(self):
        entry = Entry.create_entry("example.com", "alice", "note")
        self.assertEqual(entry.to_string(), "(example.com, alice)")

    def test_to_string_with_description(self):
        entry = Entry.create_entry("example.com", "alice", "note")
        self.assertEqual(
            entry.to_string_with_desc(),
            "Website: example.com\nUsername: alice\nDescription: note",
        )

    def test_get_json_without_totp(self):
        entry = Entry.create_entry("example.com", "alice", "note")
        self.assertEqual(
            entry.get_json(),
            {
                "website": "example.com",
                "username": "alice",
                "description": "note",
                "totp_config": {},
            },
        )

    def test_get_json_with_totp(self):
        config = TOTP_Config("issuer", "account")
        entry = Entry.create_entry("example.com", "alice", "note", config)
        self.assertEqual(entry.get_json()["totp_config"], config.to_json())

    def test_from_json_reads_entry_identity_fields(self):
        entry = Entry.from_json(
            {"website": "example.com", "username": "alice", "description": "note"}
        )
        self.assertIsNotNone(entry)
        self.assertEqual(entry.get_website(), "example.com")  # type: ignore[union-attr]
        self.assertIsNone(entry.get_totp_config())  # type: ignore[union-attr]

    def test_from_json_does_not_restore_totp_config(self):
        source = Entry.create_entry(
            "example.com", "alice", "note", TOTP_Config("issuer", "account")
        )
        restored = Entry.from_json(source.get_json())
        self.assertIsNotNone(restored)
        self.assertIsNone(restored.get_totp_config())  # type: ignore[union-attr]

    def test_from_json_ignores_extra_fields(self):
        entry = Entry.from_json(
            {
                "website": "example.com",
                "username": "alice",
                "description": "note",
                "totp_config": ["not", "used", "for", "loading"],
                "extra": 42,
            }
        )
        self.assertIsNotNone(entry)

    def test_from_json_rejects_missing_fields(self):
        self.assertIsNone(Entry.from_json({"website": "example.com"}))

    def test_from_json_rejects_non_string_entry_fields(self):
        self.assertIsNone(
            Entry.from_json({"website": 1, "username": "alice", "description": "note"})
        )

    def test_from_json_rejects_non_dictionary(self):
        self.assertIsNone(Entry.from_json([]))  # type: ignore[arg-type]
