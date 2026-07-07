import unittest
from unittest.mock import patch

from pyperclip import PyperclipException

from cli.input import (
	_handle_keystroke,
	is_backspace,
	is_ctrl_c,
	is_enter,
	poll_for_with_backspace,
	poll_y_n_backspace,
	safe_copy,
)


class CliInputTests(unittest.TestCase):
	def test_key_classification_helpers(self):
		self.assertTrue(is_backspace("\x08"))
		self.assertTrue(is_backspace("\x7f"))
		self.assertFalse(is_backspace("a"))
		self.assertTrue(is_enter("\r"))
		self.assertFalse(is_enter("\n"))
		self.assertTrue(is_ctrl_c("\x03"))
		self.assertFalse(is_ctrl_c("c"))

	def test_handle_keystroke_marks_enter_as_done(self):
		self.assertEqual(_handle_keystroke("abc", "\r"), ("abc", False, True))

	def test_handle_keystroke_removes_one_character_on_backspace(self):
		self.assertEqual(_handle_keystroke("abc", "\x08"), ("ab", True, False))
		self.assertEqual(_handle_keystroke("", "\x08"), ("", False, False))

	def test_handle_keystroke_accepts_allowed_characters_and_preserves_original_case(self):
		self.assertEqual(_handle_keystroke("", "a"), ("a", False, False))
		self.assertEqual(_handle_keystroke("", "A"), ("A", False, False))
		self.assertEqual(_handle_keystroke("", "7"), ("7", False, False))
		self.assertEqual(_handle_keystroke("", "!"), ("!", False, False))
		self.assertEqual(_handle_keystroke("hello", " "), ("hello ", False, False))

	def test_handle_keystroke_ignores_unhandled_characters(self):
		self.assertEqual(_handle_keystroke("abc", "\t"), ("abc", False, False))

	def test_poll_y_n_backspace_ignores_other_keys_until_valid_key(self):
		with patch("cli.input.get_key", side_effect=["x", "n"]):
			self.assertEqual(poll_y_n_backspace(), "n")

		with patch("cli.input.get_key", side_effect=["x", "\x08"]):
			self.assertEqual(poll_y_n_backspace(), "\x08")

	def test_poll_for_with_backspace_ignores_other_keys_until_allowed_key(self):
		with patch("cli.input.get_key", side_effect=["x", "a"]):
			self.assertEqual(poll_for_with_backspace(["a", "b"]), "a")

		with patch("cli.input.get_key", side_effect=["x", "\x7f"]):
			self.assertEqual(poll_for_with_backspace(["a", "b"]), "\x7f")

	def test_safe_copy_uses_pyperclip_when_available(self):
		with patch("cli.input.copy") as copy_mock:
			self.assertTrue(safe_copy("secret"))

		copy_mock.assert_called_once_with("secret")

	def test_safe_copy_falls_back_to_termux_clipboard(self):
		with patch("cli.input.copy", side_effect=PyperclipException("missing clipboard")):
			with patch("cli.input.subprocess.run") as run_mock:
				self.assertTrue(safe_copy("secret"))

		run_mock.assert_called_once_with(
			["termux-clipboard-set"],
			input="secret",
			text=True,
			check=True,
		)

	def test_safe_copy_returns_false_when_all_copy_methods_fail(self):
		with patch("cli.input.copy", side_effect=PyperclipException("missing clipboard")):
			with patch("cli.input.subprocess.run", side_effect=RuntimeError("no termux")):
				self.assertFalse(safe_copy("secret"))


if __name__ == "__main__":
	unittest.main()
