import unittest

from core.entry import Entry
from core.errors import EntryHasNoTotp, InvalidEntryJSON
from core.totp import TOTP_Config


class EntryTests(unittest.TestCase):
    def test_create_entry_sets_fields(self):
        entry = Entry.create_entry("example.com", "alice", "personal")

        self.assertEqual(entry.get_website(), "example.com")
        self.assertEqual(entry.get_username(), "alice")
        self.assertEqual(entry.get_description(), "personal")
        self.assertFalse(entry.has_totp())

    def test_setters_update_fields(self):
        entry = Entry.create_entry("old.com", "old-user", "old-desc")

        entry.set_website("new.com")
        entry.set_username("new-user")
        entry.set_description("new-desc")

        self.assertEqual(entry.get_website(), "new.com")
        self.assertEqual(entry.get_username(), "new-user")
        self.assertEqual(entry.get_description(), "new-desc")

    def test_get_totp_config_raises_when_missing(self):
        entry = Entry.create_entry("example.com", "alice")

        with self.assertRaises(EntryHasNoTotp):
            entry.get_totp_config()

    def test_totp_config_can_be_set_and_cleared(self):
        entry = Entry.create_entry("example.com", "alice")
        config = TOTP_Config(issuer="Example", account="alice")

        entry.set_totp_config(config)
        self.assertTrue(entry.has_totp())
        self.assertIs(entry.get_totp_config(), config)

        entry.set_totp_config(None)
        self.assertFalse(entry.has_totp())

    def test_is_equal_ignores_case_whitespace_and_description(self):
        left = Entry.create_entry(" GitHub.COM ", " Alice ", "one")
        right = Entry.create_entry("github.com", "alice", "two")

        self.assertTrue(left.is_equal(right))

    def test_is_equal_rejects_different_website_or_username(self):
        base = Entry.create_entry("example.com", "alice")

        self.assertFalse(base.is_equal(Entry.create_entry("other.com", "alice")))
        self.assertFalse(base.is_equal(Entry.create_entry("example.com", "bob")))

    def test_formatted_helpers(self):
        entry = Entry.create_entry("example.com", "alice", "personal")

        self.assertEqual(entry.get_website_username_pair_string(), "(example.com, alice)")
        self.assertEqual(
            entry.get_formatted_entry_string(),
            "Website: example.com\nUsername: alice\nDescription: personal",
        )

    def test_get_json_without_totp(self):
        entry = Entry.create_entry("example.com", "alice", "personal")

        self.assertEqual(
            entry.get_json(),
            {
                "website": "example.com",
                "username": "alice",
                "description": "personal",
                "totp_config": {},
            },
        )

    def test_get_json_with_totp(self):
        config = TOTP_Config(issuer="Example", account="alice")
        entry = Entry.create_entry("example.com", "alice", "personal", config)

        self.assertEqual(entry.get_json()["totp_config"], config.to_json())

    def test_from_json_builds_entry(self):
        entry = Entry.from_json({
            "website": "example.com",
            "username": "alice",
            "description": "personal",
        })

        self.assertEqual(entry.get_website(), "example.com")
        self.assertEqual(entry.get_username(), "alice")
        self.assertEqual(entry.get_description(), "personal")

    def test_from_json_rejects_missing_or_wrong_typed_fields(self):
        invalid_values = [
            {},
            {"website": "example.com", "username": "alice"},
            {"website": 123, "username": "alice", "description": ""},
            None,
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(InvalidEntryJSON):
                    Entry.from_json(value)


if __name__ == "__main__":
    unittest.main()
