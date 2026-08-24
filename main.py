from kivy.utils import platform
import sys

from gui.main import SimplePasswordManagerApp
from cli.main import main

if __name__ == "__main__":
    if platform == "android":
        SimplePasswordManagerApp().run()
    else:
        argv = sys.argv

        """
            If no args were provided, we run the gui
            Otherwise, we pass the args to the cli
        """
        if len(argv) < 2:
            SimplePasswordManagerApp().run()
        else:
            main(argv)