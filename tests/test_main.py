import unittest
from unittest.mock import patch

import main
from core.entry import Entry
from core.pwd_manager import PwdManager


class MainTests(unittest.TestCase):
	def test_init_rejects_invalid_number_of_arguments(self):
		with patch("builtins.print"):
			self.assertEqual(main._init(["main.py"]), 1)
			self.assertEqual(main._init(["main.py", "a", "b", "c", "d"]), 1)

	def test_init_loads_existing_vault_when_only_path_is_given(self):
		manager = PwdManager()

		with patch("main.load_vault", return_value=manager) as load_mock:
			self.assertIs(main._init(["main.py", "vault.vault"]), manager)

		load_mock.assert_called_once_with("vault.vault")

	def test_init_returns_error_when_loading_existing_vault_fails(self):
		with patch("main.load_vault", return_value=None):
			with patch("builtins.print"):
				self.assertEqual(main._init(["main.py", "vault.vault"]), -1)

	def test_init_creates_new_vault_when_extra_argument_is_given_and_file_does_not_exist(self):
		manager = PwdManager()

		with patch("main.vault_exists", return_value=False) as exists_mock:
			with patch("main.create_and_load_vault", return_value=manager) as create_mock:
				with patch("main.delete_vault") as delete_mock:
					self.assertIs(main._init(["main.py", "vault.vault", "--create"]), manager)

		exists_mock.assert_called_once_with("vault.vault")
		create_mock.assert_called_once_with("vault.vault")
		delete_mock.assert_not_called()

	def test_init_existing_vault_create_path_cancelled_by_user(self):
		with patch("main.vault_exists", return_value=True):
			with patch("main.act.double_check_deletion", return_value=False):
				with patch("main.delete_vault") as delete_mock:
					with patch("main.create_and_load_vault") as create_mock:
						with patch("builtins.print"):
							self.assertEqual(main._init(["main.py", "vault.vault", "--create"]), 0)

		delete_mock.assert_not_called()
		create_mock.assert_not_called()

	def test_init_existing_vault_create_path_deletes_then_creates_when_confirmed(self):
		manager = PwdManager()

		with patch("main.vault_exists", return_value=True):
			with patch("main.act.double_check_deletion", return_value=True):
				with patch("main.delete_vault") as delete_mock:
					with patch("main.create_and_load_vault", return_value=manager) as create_mock:
						self.assertIs(main._init(["main.py", "vault.vault", "--create"]), manager)

		delete_mock.assert_called_once_with("vault.vault")
		create_mock.assert_called_once_with("vault.vault")

	def test_init_returns_error_when_create_and_load_fails(self):
		with patch("main.vault_exists", return_value=False):
			with patch("main.create_and_load_vault", return_value=None):
				with patch("builtins.print"):
					self.assertEqual(main._init(["main.py", "vault.vault", "--create"]), -1)

	def test_sub_loop_returns_false_for_invalid_index(self):
		manager = PwdManager()

		with patch("main.clear_screen"):
			self.assertFalse(main._sub_loop(manager, "0", 0))

	def test_sub_loop_calls_specific_entry_options_for_valid_index(self):
		manager = PwdManager()
		manager.add_entry("example.com", "alice", "secret", "desc")
		entry = manager.get_entry_by_index(0)

		with patch("main.clear_screen"):
			with patch("main._specific_entry_options", return_value=True) as options_mock:
				self.assertTrue(main._sub_loop(manager, "0", 0))

		options_mock.assert_called_once_with(manager, entry)

	def test_specific_entry_options_delegates_to_selected_action(self):
		manager = PwdManager()
		entry = Entry.create_entry("example.com", "alice", "desc")

		with patch("main.poll_for_with_backspace", return_value="m"):
			with patch("main.act.modify_entry", return_value=True) as modify_mock:
				self.assertTrue(main._specific_entry_options(manager, entry))
		modify_mock.assert_called_once_with(manager, entry)

		with patch("main.poll_for_with_backspace", return_value="d"):
			with patch("main.act.remove_entry", return_value=True) as remove_mock:
				self.assertTrue(main._specific_entry_options(manager, entry))
		remove_mock.assert_called_once_with(manager, entry)

		with patch("main.poll_for_with_backspace", return_value="r"):
			with patch("main.act.get_password") as get_password_mock:
				self.assertFalse(main._specific_entry_options(manager, entry))
		get_password_mock.assert_called_once_with(manager, entry)

		with patch("main.poll_for_with_backspace", return_value="\x08"):
			self.assertFalse(main._specific_entry_options(manager, entry))


if __name__ == "__main__":
	unittest.main()
