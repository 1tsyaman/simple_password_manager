import unittest
from unittest.mock import patch

from cli.display import (
    BLUE,
    FOOTER,
    GREEN,
    HEADER,
    RED,
    RESET,
    YELLOW,
    clear_screen,
    display_list,
    display_list_str,
    print_footer,
    str_color,
)


class CliDisplayTests(unittest.TestCase):
    def test_display_list_str_formats_first_page(self):
        options, output = display_list_str(["a", "b", "c"])

        self.assertEqual(options, ["0", "1", "2"])
        self.assertEqual(output, "[0]:\ta\n[1]:\tb\n[2]:\tc")

    def test_display_list_str_formats_later_page(self):
        values = [f"item-{i}" for i in range(15)]

        options, output = display_list_str(values, index=1)

        self.assertEqual(options, ["0", "1", "2", "3", "4"])
        self.assertEqual(
            output,
            "\n".join(
                [
                    "[0]:\titem-10",
                    "[1]:\titem-11",
                    "[2]:\titem-12",
                    "[3]:\titem-13",
                    "[4]:\titem-14",
                ]
            ),
        )

    def test_display_list_str_rejects_negative_page(self):
        with self.assertRaises(IndexError):
            display_list_str(["a"], index=-1)

    def test_display_list_prints_output_and_returns_options(self):
        with patch("builtins.print") as print_mock:
            options = display_list(["a", "b"])

        self.assertEqual(options, ["0", "1"])
        print_mock.assert_called_once_with("[0]:\ta\n[1]:\tb")

    def test_str_color_wraps_known_colors(self):
        self.assertEqual(str_color("x", "r"), f"{RED}x{RESET}")
        self.assertEqual(str_color("x", "g"), f"{GREEN}x{RESET}")
        self.assertEqual(str_color("x", "y"), f"{YELLOW}x{RESET}")
        self.assertEqual(str_color("x", "b"), f"{BLUE}x{RESET}")

    def test_str_color_leaves_unknown_color_unchanged(self):
        self.assertEqual(str_color("x", "unknown"), "x")

    def test_clear_screen_invokes_os_command_and_optional_header(self):
        with patch("cli.display.os.system") as system:
            with patch("builtins.print") as print_mock:
                clear_screen(header=True)

        system.assert_called_once()
        print_mock.assert_called_once_with(HEADER)

        with patch("cli.display.os.system"):
            with patch("builtins.print") as print_mock:
                clear_screen(header=False)

        print_mock.assert_not_called()

    def test_print_footer(self):
        with patch("builtins.print") as print_mock:
            print_footer()

        print_mock.assert_called_once_with(FOOTER)


if __name__ == "__main__":
    unittest.main()
