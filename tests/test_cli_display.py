import unittest
from unittest.mock import patch

from cli.display import BLUE, GREEN, HEADER, RED, RESET, YELLOW, clear_screen, display_list, display_list_str, str_color


class CliDisplayTests(unittest.TestCase):
	def test_display_list_str_empty_list(self):
		options, output = display_list_str([])

		self.assertEqual(options, [])
		self.assertEqual(output, "")

	def test_display_list_str_first_page_contains_up_to_ten_items(self):
		items = [f"item-{i}" for i in range(12)]

		options, output = display_list_str(items, index=0)

		self.assertEqual(options, [str(i) for i in range(10)])
		self.assertEqual(output.splitlines()[0], "[0]:\titem-0")
		self.assertEqual(output.splitlines()[-1], "[9]:\titem-9")
		self.assertFalse(output.endswith("\n"))

	def test_display_list_str_second_page_restarts_visible_option_numbers(self):
		items = [f"item-{i}" for i in range(12)]

		options, output = display_list_str(items, index=1)

		self.assertEqual(options, ["0", "1"])
		self.assertEqual(output, "[0]:\titem-10\n[1]:\titem-11")

	def test_display_list_str_rejects_negative_index(self):
		with self.assertRaises(IndexError):
			display_list_str(["a"], index=-1)

	def test_display_list_prints_output_and_returns_options(self):
		with patch("builtins.print") as print_mock:
			options = display_list(["a", "b"], index=0)

		self.assertEqual(options, ["0", "1"])
		print_mock.assert_called_once_with("[0]:\ta\n[1]:\tb")

	def test_str_color_wraps_known_colors(self):
		self.assertEqual(str_color("x", "r"), f"{RED}x{RESET}")
		self.assertEqual(str_color("x", "g"), f"{GREEN}x{RESET}")
		self.assertEqual(str_color("x", "y"), f"{YELLOW}x{RESET}")
		self.assertEqual(str_color("x", "b"), f"{BLUE}x{RESET}")

	def test_str_color_returns_input_for_unknown_color(self):
		self.assertEqual(str_color("x", "unknown"), "x")

	def test_clear_screen_calls_platform_command_and_prints_header(self):
		with patch("cli.display.os.system") as system_mock, patch("builtins.print") as print_mock:
			clear_screen()

		system_mock.assert_called_once()
		print_mock.assert_called_once_with(HEADER)


if __name__ == "__main__":
	unittest.main()
