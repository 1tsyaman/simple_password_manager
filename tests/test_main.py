import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = PROJECT_ROOT / "main.py"


class MainDispatchTests(unittest.TestCase):
    def test_no_arguments_runs_gui(self):
        app = Mock()
        fake_gui_main = types.ModuleType("gui.main")
        fake_gui_main.SimplePasswordManagerApp = Mock(return_value=app)

        with patch.object(sys, "argv", ["main.py"]):
            with patch.dict(sys.modules, {"gui.main": fake_gui_main}):
                runpy.run_path(str(MAIN_PATH), run_name="__main__")

        fake_gui_main.SimplePasswordManagerApp.assert_called_once_with()
        app.run.assert_called_once_with()

    def test_arguments_are_forwarded_to_cli(self):
        fake_cli_main = types.ModuleType("cli.main")
        fake_cli_main.main = Mock()

        argv = ["main.py", "vault.vault", "--create"]

        with patch.object(sys, "argv", argv):
            with patch.dict(sys.modules, {"cli.main": fake_cli_main}):
                runpy.run_path(str(MAIN_PATH), run_name="__main__")

        fake_cli_main.main.assert_called_once_with(argv)


if __name__ == "__main__":
    unittest.main()
