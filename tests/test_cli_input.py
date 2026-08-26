import unittest
from unittest.mock import patch

from pyperclip import PyperclipException

import cli.input as cli_input


class CliInputTests(unittest.TestCase):
    def test_key_classification_helpers(self):
        self.assertTrue(cli_input.is_backspace("\x08"))
        self.assertTrue(cli_input.is_backspace("\x7f"))
        self.assertFalse(cli_input.is_backspace("a"))

        self.assertTrue(cli_input.is_enter("\r"))
        self.assertFalse(cli_input.is_enter("\n"))

        self.assertTrue(cli_input.is_ctrl_c("\x03"))
        self.assertFalse(cli_input.is_ctrl_c("c"))

    def test_handle_keystroke_appends_valid_character(self):
        with patch("cli.watchdog.reset_timer"):
            result = cli_input._handle_keystroke("ab", "C")

        self.assertEqual(result, ("abC", False, False))

    def test_handle_keystroke_handles_backspace(self):
        with patch("cli.watchdog.reset_timer"):
            self.assertEqual(
                cli_input._handle_keystroke("abc", "\x7f"),
                ("ab", True, False),
            )
            self.assertEqual(
                cli_input._handle_keystroke("", "\x7f"),
                ("", False, False),
            )

    def test_handle_keystroke_handles_enter(self):
        with patch("cli.watchdog.reset_timer"):
            self.assertEqual(
                cli_input._handle_keystroke("query", "\r"),
                ("query", False, True),
            )

    def test_handle_keystroke_ignores_invalid_character(self):
        with patch("cli.watchdog.reset_timer"):
            self.assertEqual(
                cli_input._handle_keystroke("query", "\n"),
                ("query", False, False),
            )

    def test_poll_y_n_backspace_ignores_other_keys(self):
        with patch(
            "cli.input.get_key",
            side_effect=["x", "1", "y"],
        ):
            self.assertEqual(cli_input.poll_y_n_backspace(), "y")

    def test_poll_for_with_backspace_ignores_other_keys(self):
        with patch(
            "cli.input.get_key",
            side_effect=["x", "2"],
        ):
            self.assertEqual(
                cli_input.poll_for_with_backspace(["1", "2"]),
                "2",
            )

    def test_safe_copy_returns_true_when_pyperclip_succeeds(self):
        with patch("cli.input.copy") as copy:
            self.assertTrue(cli_input.safe_copy("secret"))

        copy.assert_called_once_with("secret")

    def test_safe_copy_falls_back_to_termux(self):
        with patch(
            "cli.input.copy",
            side_effect=PyperclipException("unavailable"),
        ):
            with patch("cli.input.subprocess.run") as run:
                self.assertTrue(cli_input.safe_copy("secret"))

        run.assert_called_once_with(
            ["termux-clipboard-set"],
            input="secret",
            text=True,
            check=True,
        )

    def test_safe_copy_returns_false_when_both_backends_fail(self):
        with patch(
            "cli.input.copy",
            side_effect=PyperclipException("unavailable"),
        ):
            with patch(
                "cli.input.subprocess.run",
                side_effect=OSError("missing"),
            ):
                self.assertFalse(cli_input.safe_copy("secret"))

    def test_get_input_wraps_builtin_input(self):
        with patch("builtins.input", return_value="value") as input_mock:
            with patch("cli.watchdog.reset_timer"):
                self.assertEqual(cli_input.get_input("Prompt: "), "value")

        input_mock.assert_called_once_with("Prompt: ")

    def test_input_password_wraps_getpass(self):
        with patch("cli.input.getpass", return_value="secret") as getpass_mock:
            with patch("cli.watchdog.reset_timer"):
                self.assertEqual(
                    cli_input.input_password("Password: "),
                    "secret",
                )

        getpass_mock.assert_called_once_with("Password: ")


if __name__ == "__main__":
    unittest.main()
