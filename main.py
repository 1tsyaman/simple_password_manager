import sys
import os
from time import sleep
from pyperclip import copy
from pathlib import Path
from getpass import getpass

from pwd_manager import PwdManager, NO_SUCH_ENTRY_MESSAGE
 

"""
	This function is os-specific
"""
def get_key() -> str:
	if os.name == "nt":					# if os is windows 
		import msvcrt

		key = msvcrt.getch().decode("utf-8").lower()

		if key == "\x03":	# ctrl + c
			raise KeyboardInterrupt

		return key
								# otherwise (posix)
	import termios
	from tty import setraw

	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)

	try:
		setraw(fd)
		key =  sys.stdin.read(1).lower()

		if key == "\x03":
			raise KeyboardInterrupt

		return key
	finally:
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def add_entry(pwd_manager: PwdManager) -> None:
	clear_screen()

	website = input("Enter website:\n")
	username = input("Enter username:\n")
	password = input("Enter password:\n")
	description = input("Enter description:\n")

	while (True):
		ans: str = input(f"Save the following entry? Y/n\n {website = }\n{username = }\n{password = }\n{description = }.\n")

		match ans.lower():
			case "y":
				pwd_manager.add_entry(website, username, password, description)
				return
			case "n":
				return

def remove_entry(pwd_manager: PwdManager) -> None:
	clear_screen()

	while (True):
		website = input("Enter website:\n")
		username = input("Enter username, or press enter to delete all 'website' entries:\n")

		if (username == ""):
			message = "*all users*"
		else:
			message = f"{username}"
		ans = input(f"Deleting {message} of website {website}. Are you sure? Y/n\n")
		
		if ans.lower() == "y":
			pwd_manager.remove_entry(website, username)
		else:
			print("Operation canceled.")
		
		ans = input("Press enter to continue, or type 'back' to go back to the menu.\n")

		if ans == "back":
			return

def get_password(pwd_manager: PwdManager) -> None:
	clear_screen()

	while (True):
		website = input("Enter website:\n")
		username = input("Enter username:\n")
		pwd = pwd_manager.get_password(website, username)
		print(pwd)
		
		if pwd != NO_SUCH_ENTRY_MESSAGE:
			if input("Input '1' to copy password to clipboard.\n").strip() == '1':
				copy(pwd)
				print("Password is copied to clipboard!")

		ans = input("Press enter to continue, or type 'back' to go back to the menu.\n")

		if ans == "back":
			return

def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
	if len(sys.argv) < 2 or len(sys.argv) > 4:
		print("Usage: python this_script.py path/to/vault (--create)")
		sys.exit(1)

	
	path = sys.argv[1]

	if len(sys.argv) == 2:
		if not Path(path).exists():
			print("Vault path is incorrect")
			sys.exit(1)
		
		pwd_manager = PwdManager.from_encrypted_file(path)
		
		if not pwd_manager:
			print("Something went wrong. Exiting..")
			sys.exit(1)

	else:
		if (Path(path).exists()):
			print("Vault already exists. Overwrite it? Y/n")

			if get_key() == "y":
				print("Permanently delete the given vault? Y/n")
				if get_key() == "y":
					os.remove(Path(path))
				else:
					sys.exit(0)
			else:
				sys.exit(0)

		Path.touch(Path(path))

		pwd = getpass("Enter your master password:")
		pwd_manager = PwdManager.pwd_manager_from_pwd(path, pwd)

	try:
		while (True):
			clear_screen()

			print("Press [a] to add entry, [d] to delete entry, [r] to retrieve password or [q] to exit\n")
			ans = get_key()
			match ans:
				case "q":
					pwd_manager.encrypt_and_exit()
					sys.exit(0)
				case "a":
					add_entry(pwd_manager)
				case "d":
					remove_entry(pwd_manager)
				case "r":
					get_password(pwd_manager)
	except KeyboardInterrupt:
		print("Save before quiting? Y/n")
		if get_key() == "y":
			pwd_manager.encrypt_and_exit()
		print("Goodbye")
		sys.exit(0)
