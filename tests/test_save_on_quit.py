import unittest
from unittest.mock import patch

import cli.main as cli_main
from core.errors import KeyLengthError
from core.keys import KEY_LEN, SALT_LEN
from core.pwd_manager import PwdManager


class SaveOnQuitTests(unittest.TestCase):
    def make_manager(self):
        return PwdManager(
            path="vault.vault",
            key=b"k" * KEY_LEN,
            salt=b"s" * SALT_LEN,
        )

    def test_ctrl_c_saves_when_user_confirms(self):
        manager = self.make_manager()

        with patch("cli.main._init", return_value=manager):
            with patch("cli.main._main_loop", side_effect=KeyboardInterrupt):
                with patch("cli.main.timeout_occurred", return_value=False):
                    with patch("cli.main.get_key", return_value="y"):
                        with patch.object(manager, "encrypt") as encrypt:
                            with patch(
                                "cli.main.quit_program",
                                side_effect=SystemExit(0),
                            ):
                                with patch("cli.main.sleep"):
                                    with self.assertRaises(SystemExit):
                                        cli_main.main(["main.py", "vault.vault"])

        encrypt.assert_called_once_with()

    def test_ctrl_c_does_not_save_when_user_declines(self):
        manager = self.make_manager()

        with patch("cli.main._init", return_value=manager):
            with patch("cli.main._main_loop", side_effect=KeyboardInterrupt):
                with patch("cli.main.timeout_occurred", return_value=False):
                    with patch("cli.main.get_key", return_value="n"):
                        with patch.object(manager, "encrypt") as encrypt:
                            with patch(
                                "cli.main.quit_program",
                                side_effect=SystemExit(0),
                            ):
                                with patch("cli.main.sleep"):
                                    with self.assertRaises(SystemExit):
                                        cli_main.main(["main.py", "vault.vault"])

        encrypt.assert_not_called()

    def test_second_ctrl_c_during_prompt_quits_without_saving(self):
        manager = self.make_manager()

        with patch("cli.main._init", return_value=manager):
            with patch("cli.main._main_loop", side_effect=KeyboardInterrupt):
                with patch("cli.main.timeout_occurred", return_value=False):
                    with patch("cli.main.get_key", side_effect=KeyboardInterrupt):
                        with patch.object(manager, "encrypt") as encrypt:
                            with patch(
                                "cli.main.quit_program",
                                side_effect=SystemExit(0),
                            ):
                                with patch("cli.main.sleep"):
                                    with self.assertRaises(SystemExit):
                                        cli_main.main(["main.py", "vault.vault"])

        encrypt.assert_not_called()

    def test_save_failure_is_handled_before_quitting(self):
        manager = self.make_manager()

        with patch("cli.main._init", return_value=manager):
            with patch("cli.main._main_loop", side_effect=KeyboardInterrupt):
                with patch("cli.main.timeout_occurred", return_value=False):
                    with patch("cli.main.get_key", return_value="y"):
                        with patch.object(
                            manager,
                            "encrypt",
                            side_effect=KeyLengthError,
                        ):
                            with patch(
                                "cli.main.quit_program",
                                side_effect=SystemExit(0),
                            ):
                                with patch("cli.main.sleep"):
                                    with self.assertRaises(SystemExit):
                                        cli_main.main(["main.py", "vault.vault"])

    def test_timeout_quits_without_save_prompt(self):
        manager = self.make_manager()

        with patch("cli.main._init", return_value=manager):
            with patch("cli.main._main_loop", side_effect=KeyboardInterrupt):
                with patch("cli.main.timeout_occurred", return_value=True):
                    with patch("cli.main.get_key") as get_key:
                        with patch(
                            "cli.main.quit_program",
                            side_effect=SystemExit(0),
                        ) as quit_program:
                            with patch("cli.main.sleep"):
                                with self.assertRaises(SystemExit):
                                    cli_main.main(["main.py", "vault.vault"])

        get_key.assert_not_called()
        quit_program.assert_called_once()


if __name__ == "__main__":
    unittest.main()
