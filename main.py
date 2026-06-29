import sys
import os
from time import sleep
from pyperclip import copy
from pathlib import Path
from getpass import getpass

from pwd_manager import PwdManager, NO_SUCH_ENTRY_MESSAGE, DIGITS
 

CTRL_C		= '\x03'
ENTER		= '\r'
BACKSPACE	= '\x08'


"""
	This function is os-specific
"""
def get_key() -> str:
	if os.name == "nt":					# if os is windows 
		import msvcrt

		key = msvcrt.getch().decode("utf-8").lower()

		if key == CTRL_C:	# ctrl + c
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
	while (True):
		clear_screen()

		website_list = pwd_manager.get_website_list()

		if len(website_list) == 0:
			print("Vault has no entries. Press any button to continue.")
			get_key()

			return

		index = 0

		while True:
			new_index = display_list(website_list, index)

			key = get_key()

			if is_valid_index(key, len(website_list)):
				website = website_list[int(key)]
				break					# we can resume with account choice
			if key=='n' and new_index != index:
				index = new_index
				continue
			if key=='p' and index > 0:
				index -= 1
				continue
			if key=='q':
				return

		index = 0

		while True:
			uname_desc_list = pwd_manager.get_username_and_description(website)
		
			if len(uname_desc_list) == 0:
				print("Website has no entries. Press any button to continue.")
				get_key()

				return

			new_index = display_list(uname_desc_list, index)

			key = get_key()

			if is_valid_index(key, len(uname_desc_list)):
				username, _ = uname_desc_list[int(key)]
				break						# we can continue to grabbing the password
			if key=='n' and new_index != index:
				index = new_index
				continue
			if key=='p' and index > 0:
				index -= 1
				continue
			if key=='q':
				return

		pwd = pwd_manager.get_password(website, username)
		print(f"Password: {pwd}")

		if pwd != NO_SUCH_ENTRY_MESSAGE:
			print("Press [c] to copy password to clipboard.")
			if get_key().strip() == 'c':
				copy(pwd)
				print("Password is copied to clipboard!")


		print("Press [enter] to continue, or [backspace] to go back to the menu.\n")

		key = get_key()

		if key == BACKSPACE:
			return



def is_valid_index(key: str, bound: int) -> bool:
	return key in DIGITS and int(key) < bound

def display_list(ls: list, index=0) -> int:
	if index < 0:
		raise IndexError("Calling display_list with negative index.")
	
	start_index = 10 * index
	end_index = min(start_index + 10, len(ls))

	for i in range(start_index, end_index):
		print(f"[{i}]:\t{ls[i]}")
	
	next_page = "[n]: Next page"
	prev_page = "[p]: Previous page"

	if index == 0:
		next_page = ""
	if (index + 1) * 10 > len(ls):
		prev_page = ""
	else:
		index += 1

	print(f"[q]: Quit to main menu {next_page} {prev_page}")

	return index

def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
	try:
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

			Path(path).touch()

			pwd = getpass("Enter your master password:")
			pwd_manager = PwdManager.pwd_manager_from_pwd(path, pwd)

		try:
			while (True):
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
			print("Save before quitting? Y/n")

			try:
				if get_key() == "y":
					pwd_manager.encrypt_and_exit()
			except KeyboardInterrupt:				# in case CTRL+C is pressed again, we just quit without saving
				pass

			print("Goodbye")
			sys.exit(0)
	
	#	big net to avoid crashing
	except Exception as e:
		print("Something went wrong. Unsaved changes will not be saved.")
		print(f"Exception: {e!r}")
		sys.exit(1)
