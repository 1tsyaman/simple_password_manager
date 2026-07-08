import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

import main


class FakeEntry:
	def to_string_with_desc(self) -> str:
		return "example.com, user, desc"


class FakePwdManager:
	def __init__(self):
		self.entry = FakeEntry()

	def get_entry_list_len(self) -> int:
		return 1

	def get_website_and_username_string(self) -> list[str]:
		return ["example.com, user"]

	def get_entry_by_index(self, index: int):
		return self.entry


class SaveOnQuitTests(unittest.TestCase):
	def run_main_loop(self, keys, polls=(), manager=None):
		manager = manager or FakePwdManager()
		key_iter = iter(keys)
		poll_iter = iter(polls)
		save_changes = Mock(return_value=True)

		with ExitStack() as stack:
			stack.enter_context(patch("main.clear_screen"))
			stack.enter_context(patch("main.display_list", return_value=["0"]))
			stack.enter_context(patch("main.print_footer"))
			stack.enter_context(patch("main.format_prev_next_str", return_value=""))
			stack.enter_context(patch("main.is_valid_index", return_value=True))
			stack.enter_context(patch("main.get_key", side_effect=lambda: next(key_iter)))
			stack.enter_context(patch("main.poll_for_with_backspace", side_effect=lambda _keys: next(poll_iter)))
			stack.enter_context(patch("main.act.save_changes", save_changes))

			with self.assertRaises(SystemExit) as cm:
				main._main_loop(manager)

		self.assertEqual(cm.exception.code, 0)
		return manager, save_changes

	def test_add_entry_is_saved_when_quitting_normally(self):
		with patch("main.act.add_entry", return_value=True):
			_, save_changes = self.run_main_loop(["a", "q"])

		save_changes.assert_called_once()

	def test_modify_master_password_is_saved_when_quitting_normally(self):
		with patch("main.act.modify_master_password", return_value=True):
			_, save_changes = self.run_main_loop(["m", "q"])

		save_changes.assert_called_once()

	def test_modify_selected_entry_is_saved_when_quitting_normally(self):
		with patch("main.act.modify_entry", return_value=True):
			_, save_changes = self.run_main_loop(["0", "q"], polls=["m"])

		save_changes.assert_called_once()

	def test_delete_selected_entry_is_saved_when_quitting_normally(self):
		with patch("main.act.remove_entry", return_value=True):
			_, save_changes = self.run_main_loop(["0", "q"], polls=["d"])

		save_changes.assert_called_once()

	def test_modify_searched_entry_is_saved_when_quitting_normally(self):
		entry = FakeEntry()

		with patch("main.act.search_entries", return_value=entry):
			with patch("main.act.modify_entry", return_value=True):
				_, save_changes = self.run_main_loop(["f", "q"], polls=["m"])

		save_changes.assert_called_once()

	def test_delete_searched_entry_is_saved_when_quitting_normally(self):
		entry = FakeEntry()

		with patch("main.act.search_entries", return_value=entry):
			with patch("main.act.remove_entry", return_value=True):
				_, save_changes = self.run_main_loop(["f", "q"], polls=["d"])

		save_changes.assert_called_once()

	def test_retrieve_password_does_not_save_when_quitting_normally(self):
		with patch("main.act.get_password") as get_password:
			_, save_changes = self.run_main_loop(["0", "q"], polls=["r"])

		get_password.assert_called_once()
		save_changes.assert_not_called()

	def test_generate_password_does_not_save_when_quitting_normally(self):
		with patch("main.act.gen_rand_password") as gen_rand_password:
			_, save_changes = self.run_main_loop(["g", "q"])

		gen_rand_password.assert_called_once()
		save_changes.assert_not_called()

	def test_manual_save_resets_modified_flag_before_quit(self):
		manager = FakePwdManager()

		with ExitStack() as stack:
			stack.enter_context(patch("main.clear_screen"))
			stack.enter_context(patch("main.display_list", return_value=["0"]))
			stack.enter_context(patch("main.print_footer"))
			stack.enter_context(patch("main.format_prev_next_str", return_value=""))
			stack.enter_context(patch("main.get_key", side_effect=["a", "s", "q"]))
			stack.enter_context(patch("main.act.add_entry", return_value=True))
			save_changes = stack.enter_context(patch("main.act.save_changes", return_value=True))

			with self.assertRaises(SystemExit):
				main._main_loop(manager)

		# Called for the explicit [s] save, but not again on [q].
		save_changes.assert_called_once_with(manager)


if __name__ == "__main__":
	unittest.main()
