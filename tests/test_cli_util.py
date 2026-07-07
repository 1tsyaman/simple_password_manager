import unittest

from cli.util import filter_list, format_prev_next_str, is_valid_index, list_diff
from core.entry import Entry


class CliUtilTests(unittest.TestCase):
	def test_is_valid_index_accepts_digit_inside_current_page_bound(self):
		self.assertTrue(is_valid_index("0", 0, 1))
		self.assertTrue(is_valid_index("9", 0, 10))
		self.assertTrue(is_valid_index("0", 1, 11))

	def test_is_valid_index_rejects_non_digits_and_out_of_bounds_values(self):
		self.assertFalse(is_valid_index("a", 0, 10))
		self.assertFalse(is_valid_index("1", 0, 1))
		self.assertFalse(is_valid_index("0", 1, 10))

	def test_format_prev_next_str_matches_current_paging_logic(self):
		self.assertEqual(format_prev_next_str(0, len=9), "")
		self.assertEqual(format_prev_next_str(0, len=11), "[n] for next page, ")
		self.assertEqual(format_prev_next_str(1, len=11), "[p] for previous page, ")
		self.assertEqual(
			format_prev_next_str(1, len=25),
			"[p] for previous page, [n] for next page, ",
		)

	def test_list_diff_removes_elements_found_in_second_list(self):
		first = [1, 2, 3, 4]
		second = [2, 4]

		self.assertEqual(list_diff(first, second), [1, 3])

	def test_filter_list_searches_description_then_website_then_username_without_duplicates(self):
		desc_match = Entry.create_entry("alpha.com", "alice", "project docs")
		website_match = Entry.create_entry("docs.example", "bob", "hosting")
		username_match = Entry.create_entry("other.com", "docs-user", "misc")
		multi_match = Entry.create_entry("docs-site.com", "docs-name", "docs desc")
		entries = [website_match, username_match, desc_match, multi_match]

		result = filter_list(entries, "docs")

		self.assertEqual(result, [desc_match, multi_match, website_match, username_match])

	def test_filter_list_is_case_insensitive(self):
		entry = Entry.create_entry("GitHub.com", "Alice", "Code Host")

		self.assertEqual(filter_list([entry], "github"), [entry])
		self.assertEqual(filter_list([entry], "ALICE"), [entry])
		self.assertEqual(filter_list([entry], "code"), [entry])


if __name__ == "__main__":
	unittest.main()
