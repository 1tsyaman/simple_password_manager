import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from entry import Entry


class EntryTests(unittest.TestCase):
    def test_create_entry_sets_all_fields(self):
        entry = Entry.create_entry("github.com", "yaman", "private repo")

        self.assertEqual(entry.get_website(), "github.com")
        self.assertEqual(entry.get_username(), "yaman")
        self.assertEqual(entry.get_description(), "private repo")

    def test_get_json_contains_public_entry_fields(self):
        entry = Entry.create_entry("github.com", "yaman", "private repo")

        self.assertEqual(
            entry.get_json(),
            {
                "website": "github.com",
                "username": "yaman",
                "description": "private repo",
            },
        )

    def test_is_equal_ignores_case_whitespace_and_description(self):
        left = Entry.create_entry(" GitHub.COM ", " Yaman ", "old description")
        right = Entry.create_entry("github.com", "yaman", "new description")

        self.assertTrue(left.is_equal(right))

    def test_is_equal_detects_different_username(self):
        left = Entry.create_entry("github.com", "yaman")
        right = Entry.create_entry("github.com", "other-user")

        self.assertFalse(left.is_equal(right))

    def test_from_json_round_trip(self):
        entry = Entry.from_json(
            {
                "website": "example.org",
                "username": "alice",
                "description": "test account",
            }
        )

        self.assertEqual(entry.get_website(), "example.org")
        self.assertEqual(entry.get_username(), "alice")
        self.assertEqual(entry.get_description(), "test account")


if __name__ == "__main__":
    unittest.main()
