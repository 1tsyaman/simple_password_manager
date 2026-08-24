import sys

if __name__ == "__main__":
        argv = sys.argv

        """
            If no args were provided (which is always the case on Android), we run the gui
            Otherwise, we pass the args to the cli
        """
        if len(argv) < 2:
            from gui.main import SimplePasswordManagerApp

            SimplePasswordManagerApp().run()
        else:
            from cli.main import main

            main(argv)