import unittest

from cli.util import filter_list, format_prev_next_str, is_valid_index, list_diff
from core.entry import Entry


class CliUtilTests(unittest.TestCase):
    def test_is_valid_index_checks_page_and_bound(self):
        self.assertTrue(is_valid_index("0", index=0, bound=1))
        self.assertTrue(is_valid_index("2", index=1, bound=13))
        self.assertFalse(is_valid_index("3", index=1, bound=13))
        self.assertFalse(is_valid_index("x", index=0, bound=10))

    def test_format_prev_next_str(self):
        self.assertEqual(
            format_prev_next_str(index=0, len=5),
            "",
        )
        self.assertEqual(
            format_prev_next_str(index=0, len=11),
            "[n] for next page, ",
        )
        self.assertEqual(
            format_prev_next_str(index=1, len=11),
            "[p] for previous page, ",
        )
        self.assertEqual(
            format_prev_next_str(index=1, len=21),
            "[p] for previous page, [n] for next page, ",
        )

    def test_list_diff_preserves_order(self):
        self.assertEqual(list_diff([1, 2, 3, 2], [2]), [1, 3])

    def test_filter_list_matches_description_website_and_username(self):
        description = Entry.create_entry("site-a", "alice", "github note")
        website = Entry.create_entry("github.com", "bob", "work")
        username = Entry.create_entry("bank", "github-user", "money")
        unrelated = Entry.create_entry("other", "carol", "none")

        result = filter_list(
            [description, website, username, unrelated],
            "GITHUB",
        )

        self.assertEqual(result, [description, website, username])

    def test_filter_list_does_not_duplicate_entry_matching_multiple_fields(self):
        entry = Entry.create_entry("github.com", "github-user", "github")

        self.assertEqual(filter_list([entry], "github"), [entry])


if __name__ == "__main__":
    unittest.main()
