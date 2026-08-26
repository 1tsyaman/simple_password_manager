import unittest
from unittest.mock import Mock, patch

import cli.actions as actions
from core.entry import Entry
from core.errors import EntryExistsError, NoSuchEntryError
from core.pwd_manager import PwdManager


class CliActionsTests(unittest.TestCase):
    def setUp(self):
        clear_screen_patcher = patch("cli.actions.clear_screen")
        sleep_patcher = patch("cli.actions.sleep")
        self.addCleanup(clear_screen_patcher.stop)
        self.addCleanup(sleep_patcher.stop)
        clear_screen_patcher.start()
        sleep_patcher.start()

    def test_add_entry_manual_password_adds_entry_after_confirmation(self):
        manager = PwdManager()

        with patch(
            "cli.actions.get_input",
            side_effect=["example.com", "alice", "secret", "desc"],
        ):
            with patch("cli.actions.get_key", return_value="n"):
                with patch("cli.actions.poll_y_n_backspace", return_value="y"):
                    self.assertTrue(actions.add_entry(manager))

        self.assertEqual(manager.get_password("example.com", "alice"), "secret")

    def test_add_entry_returns_false_when_confirmation_is_not_yes(self):
        manager = PwdManager()

        with patch(
            "cli.actions.get_input",
            side_effect=["example.com", "alice", "secret", "desc"],
        ):
            with patch("cli.actions.get_key", return_value="n"):
                with patch("cli.actions.poll_y_n_backspace", return_value="n"):
                    self.assertFalse(actions.add_entry(manager))

        self.assertEqual(manager.get_entry_list_len(), 0)

    def test_add_entry_random_password_branch_adds_generated_password(self):
        manager = PwdManager()

        with patch(
            "cli.actions.get_input",
            side_effect=["example.com", "alice", "desc"],
        ):
            with patch("cli.actions.get_key", return_value="y"):
                with patch(
                    "cli.actions.PwdManager.generate_random_pwd",
                    return_value="generated-secret",
                ):
                    with patch("cli.actions.safe_copy", return_value=False):
                        with patch(
                            "cli.actions.poll_y_n_backspace",
                            return_value="y",
                        ):
                            self.assertTrue(actions.add_entry(manager))

        self.assertEqual(
            manager.get_password("example.com", "alice"),
            "generated-secret",
        )

    def test_add_entry_handles_duplicate_exception(self):
        manager = Mock()
        manager.add_entry.side_effect = EntryExistsError

        with patch(
            "cli.actions.get_input",
            side_effect=["example.com", "alice", "secret", "desc"],
        ):
            with patch("cli.actions.get_key", return_value="n"):
                with patch("cli.actions.poll_y_n_backspace", return_value="y"):
                    self.assertFalse(actions.add_entry(manager))

    def test_remove_entry_deletes_entry_after_confirmation(self):
        manager = PwdManager()
        manager.add_entry("example.com", "alice", "secret", "desc")
        entry = manager.get_entry_by_index(0)

        with patch("cli.actions.poll_y_n_backspace", return_value="y"):
            self.assertTrue(actions.remove_entry(manager, entry))

        self.assertEqual(manager.get_entry_list_len(), 0)

    def test_remove_entry_returns_false_when_cancelled(self):
        manager = PwdManager()
        manager.add_entry("example.com", "alice", "secret", "desc")
        entry = manager.get_entry_by_index(0)

        with patch("cli.actions.poll_y_n_backspace", return_value="n"):
            self.assertFalse(actions.remove_entry(manager, entry))

        self.assertEqual(manager.get_entry_list_len(), 1)

    def test_get_password_copies_when_user_presses_c(self):
        manager = PwdManager()
        manager.add_entry("example.com", "alice", "secret", "desc")
        entry = manager.get_entry_by_index(0)

        with patch("cli.actions.get_key", return_value="c"):
            with patch("cli.actions.safe_copy", return_value=True) as copy_mock:
                actions.get_password(manager, entry)

        copy_mock.assert_called_once_with("secret")

    def test_get_password_handles_missing_entry_exception(self):
        manager = PwdManager()
        entry = Entry.create_entry("missing.com", "alice")

        with patch("builtins.print") as print_mock:
            actions.get_password(manager, entry)

        print_mock.assert_any_call(actions.NO_SUCH_ENTRY_MESSAGE)

    def test_get_totp_handles_entry_without_totp(self):
        manager = PwdManager()
        manager.add_entry("example.com", "alice", "secret", "")
        entry = manager.get_entry_by_index(0)

        with patch("builtins.print") as print_mock:
            actions.get_totp_code(manager, entry)

        print_mock.assert_any_call(actions.NO_SUCH_TOTP_MESSAGE)

    def test_modify_website_updates_entry_when_input_is_nonempty(self):
        entry = Entry.create_entry("old.com", "alice", "desc")

        with patch("cli.actions.get_input", return_value="new.com"):
            self.assertTrue(actions._modify_website(entry))

        self.assertEqual(entry.get_website(), "new.com")

    def test_modify_website_returns_false_on_empty_input(self):
        entry = Entry.create_entry("old.com", "alice", "desc")

        with patch("cli.actions.get_input", return_value=""):
            self.assertFalse(actions._modify_website(entry))

        self.assertEqual(entry.get_website(), "old.com")

    def test_modify_username_and_description_update_entry(self):
        entry = Entry.create_entry("example.com", "old-user", "old-desc")

        with patch("cli.actions.get_input", return_value="new-user"):
            self.assertTrue(actions._modify_username(entry))
        with patch("cli.actions.get_input", return_value="new-desc"):
            self.assertTrue(actions._modify_description(entry))

        self.assertEqual(entry.get_username(), "new-user")
        self.assertEqual(entry.get_description(), "new-desc")

    def test_modify_password_updates_manager_password(self):
        manager = PwdManager()
        manager.add_entry("example.com", "alice", "old-secret", "desc")
        entry = manager.get_entry_by_index(0)

        with patch("cli.actions.get_input", return_value="new-secret"):
            self.assertTrue(actions._modify_password(manager, entry))

        self.assertEqual(
            manager.get_password("example.com", "alice"),
            "new-secret",
        )

    def test_modify_password_handles_missing_entry_exception(self):
        manager = PwdManager()
        entry = Entry.create_entry("missing.com", "alice", "desc")

        with patch("cli.actions.get_input", return_value="new-secret"):
            self.assertFalse(actions._modify_password(manager, entry))

    def test_modify_master_password_updates_when_confirmed(self):
        manager = Mock()

        with patch("cli.actions.get_input", return_value="Master1!"):
            with patch("cli.actions.poll_y_n_backspace", return_value="y"):
                self.assertTrue(actions.modify_master_password(manager))

        manager.modify_master_password.assert_called_once_with("Master1!")

    def test_modify_master_password_returns_false_for_empty_input_or_cancel(self):
        manager = Mock()

        with patch("cli.actions.get_input", return_value=""):
            self.assertFalse(actions.modify_master_password(manager))

        with patch("cli.actions.get_input", return_value="Master1!"):
            with patch("cli.actions.poll_y_n_backspace", return_value="n"):
                self.assertFalse(actions.modify_master_password(manager))

    def test_save_changes_calls_encrypt_and_returns_true(self):
        manager = Mock()

        self.assertTrue(actions.save_changes(manager))

        manager.encrypt.assert_called_once_with()

    def test_save_changes_returns_false_when_backend_raises(self):
        manager = Mock()
        manager.encrypt.side_effect = FileNotFoundError("missing")

        self.assertFalse(actions.save_changes(manager))

    def test_handle_query_filters_until_enter(self):
        manager = PwdManager()
        manager.add_entry("GitHub", "alice", "secret", "code host")
        manager.add_entry("Bank", "alice", "secret", "money")

        with patch("cli.actions.get_key", side_effect=["g", "i", "\r"]):
            with patch("cli.watchdog.reset_timer"):
                result = actions.handle_query(manager)

        self.assertEqual(
            [entry.get_website() for entry in result],
            ["GitHub"],
        )

    def test_search_entries_returns_none_when_no_candidates(self):
        with patch("cli.actions.handle_query", return_value=[]):
            self.assertIsNone(actions.search_entries(PwdManager()))

    def test_search_entries_returns_selected_candidate(self):
        entry = Entry.create_entry("example.com", "alice", "desc")

        with patch("cli.actions.handle_query", return_value=[entry]):
            with patch("cli.actions.display_list", return_value=["0"]):
                with patch(
                    "cli.actions.poll_for_with_backspace",
                    return_value="0",
                ):
                    self.assertIs(actions.search_entries(PwdManager()), entry)

    def test_double_check_deletion_requires_two_yes_answers(self):
        with patch("cli.actions.get_key", side_effect=["y", "y"]):
            self.assertTrue(actions.double_check_deletion("first", "second"))

        with patch("cli.actions.get_key", side_effect=["y", "n"]):
            self.assertFalse(actions.double_check_deletion("first", "second"))

        with patch("cli.actions.get_key", side_effect=["n"]):
            self.assertFalse(actions.double_check_deletion("first", "second"))

    def test_gen_rand_password_shows_password_and_waits_for_key(self):
        with patch(
            "cli.actions.PwdManager.generate_random_pwd",
            return_value="generated-secret",
        ):
            with patch("cli.actions.safe_copy", return_value=False):
                with patch("cli.actions.get_key", return_value="x") as get_key:
                    actions.gen_rand_password()

        get_key.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
