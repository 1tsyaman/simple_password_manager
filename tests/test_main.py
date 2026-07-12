import signal
import unittest
from unittest.mock import Mock, call, patch

import main
from core.entry import Entry
from core.pwd_manager import PwdManager


class SilentOutputTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        print_patcher = patch("builtins.print")
        print_patcher.start()
        self.addCleanup(print_patcher.stop)


class MainInitializationTests(SilentOutputTestCase):
    @patch("main.init_watchdog")
    def test_rejects_too_few_arguments(self, init_watchdog: Mock) -> None:
        self.assertEqual(main._init(["main.py"]), 1)
        init_watchdog.assert_not_called()

    @patch("main.init_watchdog")
    def test_rejects_too_many_arguments(self, init_watchdog: Mock) -> None:
        self.assertEqual(
            main._init(["main.py", "vault", "--create", "extra", "argument"]),
            1,
        )
        init_watchdog.assert_not_called()

    @patch("main.load_vault")
    @patch("main.act.grab_master_password", return_value="master-password")
    @patch("main.init_watchdog")
    def test_opens_existing_vault(
        self,
        init_watchdog: Mock,
        grab_master_password: Mock,
        load_vault: Mock,
    ) -> None:
        manager = Mock(spec=PwdManager)
        load_vault.return_value = manager

        result = main._init(["main.py", "vault.vault"])

        self.assertIs(result, manager)
        init_watchdog.assert_called_once_with(exit_func=main.timeout_exit)
        grab_master_password.assert_called_once_with()
        load_vault.assert_called_once_with("vault.vault", "master-password")

    @patch("main.load_vault", return_value=None)
    @patch("main.act.grab_master_password", return_value="master-password")
    @patch("main.init_watchdog")
    def test_returns_error_when_existing_vault_cannot_be_loaded(
        self,
        init_watchdog: Mock,
        grab_master_password: Mock,
        load_vault: Mock,
    ) -> None:
        self.assertEqual(main._init(["main.py", "vault.vault"]), -1)
        init_watchdog.assert_called_once_with(exit_func=main.timeout_exit)
        grab_master_password.assert_called_once_with()
        load_vault.assert_called_once_with("vault.vault", "master-password")

    @patch("main.create_and_load_vault")
    @patch("main.delete_vault")
    @patch("main.act.grab_master_password")
    @patch("main.act.double_check_deletion", return_value=False)
    @patch("main.vault_exists", return_value=True)
    @patch("main.init_watchdog")
    def test_existing_vault_is_not_overwritten_without_confirmation(
        self,
        init_watchdog: Mock,
        vault_exists: Mock,
        double_check_deletion: Mock,
        grab_master_password: Mock,
        delete_vault: Mock,
        create_and_load_vault: Mock,
    ) -> None:
        result = main._init(["main.py", "vault.vault", "--create"])

        self.assertEqual(result, 0)
        init_watchdog.assert_called_once_with(exit_func=main.timeout_exit)
        vault_exists.assert_called_once_with("vault.vault")
        double_check_deletion.assert_called_once()
        grab_master_password.assert_not_called()
        delete_vault.assert_not_called()
        create_and_load_vault.assert_not_called()

    @patch("main.create_and_load_vault")
    @patch("main.delete_vault")
    @patch("main.act.grab_master_password", return_value="new-master-password")
    @patch("main.act.double_check_deletion", return_value=True)
    @patch("main.vault_exists", return_value=True)
    @patch("main.init_watchdog")
    def test_existing_vault_is_deleted_and_recreated_after_confirmation(
        self,
        init_watchdog: Mock,
        vault_exists: Mock,
        double_check_deletion: Mock,
        grab_master_password: Mock,
        delete_vault: Mock,
        create_and_load_vault: Mock,
    ) -> None:
        manager = Mock(spec=PwdManager)
        create_and_load_vault.return_value = manager

        result = main._init(["main.py", "vault.vault", "--create"])

        self.assertIs(result, manager)
        init_watchdog.assert_called_once_with(exit_func=main.timeout_exit)
        vault_exists.assert_called_once_with("vault.vault")
        double_check_deletion.assert_called_once()
        delete_vault.assert_called_once_with("vault.vault")
        grab_master_password.assert_called_once_with(new=True)
        create_and_load_vault.assert_called_once_with(
            "vault.vault",
            "new-master-password",
        )

    @patch("main.create_and_load_vault")
    @patch("main.delete_vault")
    @patch("main.act.grab_master_password", return_value="new-master-password")
    @patch("main.act.double_check_deletion")
    @patch("main.vault_exists", return_value=False)
    @patch("main.init_watchdog")
    def test_creates_vault_when_path_does_not_exist(
        self,
        init_watchdog: Mock,
        vault_exists: Mock,
        double_check_deletion: Mock,
        grab_master_password: Mock,
        delete_vault: Mock,
        create_and_load_vault: Mock,
    ) -> None:
        manager = Mock(spec=PwdManager)
        create_and_load_vault.return_value = manager

        result = main._init(["main.py", "vault.vault", "--create"])

        self.assertIs(result, manager)
        vault_exists.assert_called_once_with("vault.vault")
        double_check_deletion.assert_not_called()
        delete_vault.assert_not_called()
        grab_master_password.assert_called_once_with(new=True)
        create_and_load_vault.assert_called_once_with(
            "vault.vault",
            "new-master-password",
        )

    @patch("main.create_and_load_vault", return_value=None)
    @patch("main.act.grab_master_password", return_value="new-master-password")
    @patch("main.vault_exists", return_value=False)
    @patch("main.init_watchdog")
    def test_returns_error_when_new_vault_cannot_be_created(
        self,
        init_watchdog: Mock,
        vault_exists: Mock,
        grab_master_password: Mock,
        create_and_load_vault: Mock,
    ) -> None:
        self.assertEqual(
            main._init(["main.py", "vault.vault", "--create"]),
            -1,
        )
        vault_exists.assert_called_once_with("vault.vault")
        grab_master_password.assert_called_once_with(new=True)
        create_and_load_vault.assert_called_once_with(
            "vault.vault",
            "new-master-password",
        )


class MainLoopTests(SilentOutputTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.manager = Mock(spec=PwdManager)
        self.manager.get_entry_list_len.return_value = 0
        self.manager.get_website_and_username_string.return_value = []

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.get_key", return_value="q")
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_quitting_unmodified_vault_does_not_save(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        save_changes.assert_not_called()
        sleep.assert_not_called()

    @patch("main.sleep")
    @patch("main.act.save_changes", return_value=True)
    @patch("main.act.add_entry", return_value=True)
    @patch("main.get_key", side_effect=["a", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_quitting_after_addition_saves_changes(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        add_entry: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        add_entry.assert_called_once_with(self.manager)
        save_changes.assert_called_once_with(self.manager)

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.act.add_entry", return_value=False)
    @patch("main.get_key", side_effect=["a", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_cancelled_addition_does_not_mark_vault_modified(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        add_entry: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        add_entry.assert_called_once_with(self.manager)
        save_changes.assert_not_called()

    @patch("main.sleep")
    @patch("main.act.save_changes", return_value=True)
    @patch("main.act.add_entry", return_value=True)
    @patch("main.get_key", side_effect=["a", "s", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_successful_manual_save_resets_modified_state(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        add_entry: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        save_changes.assert_called_once_with(self.manager)

    @patch("main.sleep")
    @patch("main.act.save_changes", side_effect=[False, True])
    @patch("main.act.add_entry", return_value=True)
    @patch("main.get_key", side_effect=["a", "s", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_failed_manual_save_keeps_modified_state(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        add_entry: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        self.assertEqual(save_changes.call_count, 2)
        save_changes.assert_has_calls([call(self.manager), call(self.manager)])

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.act.gen_rand_password")
    @patch("main.get_key", side_effect=["g", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_password_generation_does_not_mark_vault_modified(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        gen_rand_password: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        gen_rand_password.assert_called_once_with()
        save_changes.assert_not_called()

    @patch("main.sleep")
    @patch("main.act.save_changes", return_value=True)
    @patch("main.act.modify_master_password", return_value=True)
    @patch("main.get_key", side_effect=["m", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_master_password_modification_marks_vault_modified(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        modify_master_password: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        modify_master_password.assert_called_once_with(self.manager)
        save_changes.assert_called_once_with(self.manager)

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main._specific_entry_options")
    @patch("main.act.search_entries", return_value=None)
    @patch("main.get_key", side_effect=["f", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_cancelled_search_does_not_open_entry_menu(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        search_entries: Mock,
        specific_entry_options: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        search_entries.assert_called_once_with(self.manager)
        specific_entry_options.assert_not_called()
        save_changes.assert_not_called()

    @patch("main.sleep")
    @patch("main.act.save_changes", return_value=True)
    @patch("main._specific_entry_options", return_value=True)
    @patch("main.act.search_entries")
    @patch("main.get_key", side_effect=["f", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_modification_from_search_entry_menu_is_saved_on_quit(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        search_entries: Mock,
        specific_entry_options: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        entry = Mock(spec=Entry)
        search_entries.return_value = entry

        main._main_loop(self.manager)

        specific_entry_options.assert_called_once_with(self.manager, entry)
        save_changes.assert_called_once_with(self.manager)

    @patch("main.sleep")
    @patch("main.act.save_changes", return_value=True)
    @patch("main._sub_loop", return_value=True)
    @patch("main.get_key", side_effect=["0", "q"])
    @patch("main.display_list", return_value=["0"])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_visible_entry_option_opens_sub_loop(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        sub_loop: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        self.manager.get_entry_list_len.return_value = 1
        self.manager.get_website_and_username_string.return_value = [
            "(example.com, alice)"
        ]

        main._main_loop(self.manager)

        sub_loop.assert_called_once_with(self.manager, "0", 0)
        save_changes.assert_called_once_with(self.manager)

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.get_key", side_effect=["n", "q"])
    @patch("main.display_list", side_effect=[["0"], ["0"]])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_next_page_moves_to_second_page_when_entries_exist(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        entries = [f"entry-{index}" for index in range(11)]
        self.manager.get_entry_list_len.return_value = len(entries)
        self.manager.get_website_and_username_string.return_value = entries

        main._main_loop(self.manager)

        self.assertEqual(display_list.call_args_list[0], call(entries, 0))
        self.assertEqual(display_list.call_args_list[1], call(entries, 1))

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.get_key", side_effect=["n", "q"])
    @patch("main.display_list", side_effect=[["0"], ["0"]])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_next_page_is_ignored_when_no_second_page_exists(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        entries = [f"entry-{index}" for index in range(9)]
        self.manager.get_entry_list_len.return_value = len(entries)
        self.manager.get_website_and_username_string.return_value = entries

        main._main_loop(self.manager)

        self.assertEqual(display_list.call_args_list[0], call(entries, 0))
        self.assertEqual(display_list.call_args_list[1], call(entries, 0))

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.get_key", side_effect=["n", "p", "q"])
    @patch("main.display_list", side_effect=[["0"], ["0"], ["0"]])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_previous_page_returns_to_first_page(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        entries = [f"entry-{index}" for index in range(11)]
        self.manager.get_entry_list_len.return_value = len(entries)
        self.manager.get_website_and_username_string.return_value = entries

        main._main_loop(self.manager)

        self.assertEqual(
            display_list.call_args_list,
            [
                call(entries, 0),
                call(entries, 1),
                call(entries, 0),
            ],
        )

    @patch("main.sleep")
    @patch("main.act.save_changes")
    @patch("main.get_key", side_effect=["invalid", "q"])
    @patch("main.display_list", return_value=[])
    @patch("main.print_footer")
    @patch("main.clear_screen")
    def test_unknown_key_is_ignored_without_redrawing_menu(
        self,
        clear_screen: Mock,
        print_footer: Mock,
        display_list: Mock,
        get_key: Mock,
        save_changes: Mock,
        sleep: Mock,
    ) -> None:
        main._main_loop(self.manager)

        display_list.assert_called_once_with([], 0)
        save_changes.assert_not_called()


class SubLoopTests(SilentOutputTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.manager = Mock(spec=PwdManager)
        self.manager.get_entry_list_len.return_value = 30

    @patch("main._specific_entry_options")
    @patch("main.is_valid_index", return_value=False)
    @patch("main.clear_screen")
    def test_invalid_entry_selection_is_rejected(
        self,
        clear_screen: Mock,
        is_valid_index: Mock,
        specific_entry_options: Mock,
    ) -> None:
        self.assertFalse(main._sub_loop(self.manager, "9", 2))

        is_valid_index.assert_called_once_with("9", 2, 30)
        self.manager.get_entry_by_index.assert_not_called()
        specific_entry_options.assert_not_called()

    @patch("main._specific_entry_options", return_value=True)
    @patch("main.is_valid_index", return_value=True)
    @patch("main.clear_screen")
    def test_valid_entry_selection_uses_page_offset(
        self,
        clear_screen: Mock,
        is_valid_index: Mock,
        specific_entry_options: Mock,
    ) -> None:
        entry = Mock(spec=Entry)
        self.manager.get_entry_by_index.return_value = entry

        self.assertTrue(main._sub_loop(self.manager, "3", 2))

        is_valid_index.assert_called_once_with("3", 2, 30)
        self.manager.get_entry_by_index.assert_called_once_with(23)
        specific_entry_options.assert_called_once_with(self.manager, entry)


class SpecificEntryOptionsTests(SilentOutputTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.manager = Mock(spec=PwdManager)
        self.entry = Mock(spec=Entry)
        self.entry.to_string_with_desc.return_value = "entry"

    @patch("main.act.modify_entry", return_value=True)
    @patch("main.poll_for_with_backspace", return_value="m")
    @patch("main.print_footer")
    def test_modify_option_returns_action_result(
        self,
        print_footer: Mock,
        poll_for_with_backspace: Mock,
        modify_entry: Mock,
    ) -> None:
        self.entry.has_totp.return_value = False

        self.assertTrue(main._specific_entry_options(self.manager, self.entry))

        poll_for_with_backspace.assert_called_once_with(
            ["m", "d", "r", "BACKSPACE"]
        )
        modify_entry.assert_called_once_with(self.manager, self.entry)

    @patch("main.act.remove_entry", return_value=True)
    @patch("main.poll_for_with_backspace", return_value="d")
    @patch("main.print_footer")
    def test_delete_option_returns_action_result(
        self,
        print_footer: Mock,
        poll_for_with_backspace: Mock,
        remove_entry: Mock,
    ) -> None:
        self.entry.has_totp.return_value = False

        self.assertTrue(main._specific_entry_options(self.manager, self.entry))

        remove_entry.assert_called_once_with(self.manager, self.entry)

    @patch("main.act.get_password")
    @patch("main.poll_for_with_backspace", return_value="r")
    @patch("main.print_footer")
    def test_retrieve_option_does_not_mark_vault_modified(
        self,
        print_footer: Mock,
        poll_for_with_backspace: Mock,
        get_password: Mock,
    ) -> None:
        self.entry.has_totp.return_value = False

        self.assertFalse(main._specific_entry_options(self.manager, self.entry))

        get_password.assert_called_once_with(self.manager, self.entry)

    @patch("main.act.get_totp_code")
    @patch("main.poll_for_with_backspace", return_value="g")
    @patch("main.print_footer")
    def test_totp_option_is_available_for_configured_entry(
        self,
        print_footer: Mock,
        poll_for_with_backspace: Mock,
        get_totp_code: Mock,
    ) -> None:
        self.entry.has_totp.return_value = True

        self.assertFalse(main._specific_entry_options(self.manager, self.entry))

        poll_for_with_backspace.assert_called_once_with(
            ["m", "d", "r", "BACKSPACE", "g"]
        )
        get_totp_code.assert_called_once_with(self.manager, self.entry)

    @patch("main.poll_for_with_backspace", return_value="BACKSPACE")
    @patch("main.print_footer")
    def test_backspace_returns_without_modifying_vault(
        self,
        print_footer: Mock,
        poll_for_with_backspace: Mock,
    ) -> None:
        self.entry.has_totp.return_value = False

        self.assertFalse(main._specific_entry_options(self.manager, self.entry))

    @patch("main.poll_for_with_backspace", return_value="BACKSPACE")
    @patch("main.print_footer")
    def test_totp_option_is_not_offered_for_password_only_entry(
        self,
        print_footer: Mock,
        poll_for_with_backspace: Mock,
    ) -> None:
        self.entry.has_totp.return_value = False

        main._specific_entry_options(self.manager, self.entry)

        options = poll_for_with_backspace.call_args.args[0]
        self.assertNotIn("g", options)


class ProgramLifecycleTests(SilentOutputTestCase):
    @patch("main.cancel_watchdog")
    @patch("main.clear_screen")
    def test_cleanup_clears_screen_and_cancels_watchdog(
        self,
        clear_screen: Mock,
        cancel_watchdog: Mock,
    ) -> None:
        main.cleanup()

        clear_screen.assert_called_once_with(header=False)
        cancel_watchdog.assert_called_once_with()

    @patch("main.cleanup")
    def test_quit_program_cleans_up_and_raises_system_exit(
        self,
        cleanup: Mock,
    ) -> None:
        with self.assertRaises(SystemExit) as context:
            main.quit_program(exit_code=7, message="Goodbye")

        self.assertEqual(context.exception.code, 7)
        cleanup.assert_called_once_with()

    @patch("main.os.kill")
    @patch("main.os.getpid", return_value=1234)
    def test_timeout_exit_sends_sigint_to_current_process(
        self,
        getpid: Mock,
        kill: Mock,
    ) -> None:
        main.timeout_exit()

        kill.assert_called_once_with(1234, signal.SIGINT)


if __name__ == "__main__":
    unittest.main()
