import sys
import os
import subprocess
from time import sleep
from pyperclip import copy, PyperclipException
from pathlib import Path
from getpass import getpass

from core.pwd_manager import PwdManager, NO_SUCH_ENTRY_MESSAGE, DIGITS, LETTERS_LOWER, SPECIAL_CHARS
from core.entry import Entry


CTRL_C		= '\x03'
ENTER		= '\r'
BACKSPACE	= '\x08'

CHARS = DIGITS + LETTERS_LOWER + SPECIAL_CHARS

HEADER		= f"{15*"-"} Password Manager {15*"-"}"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


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


"""
	supports copying mechanism for termux
"""
def safe_copy(text: str) -> bool:
	try:
		copy(text)
		return True
	except PyperclipException:
		try:
			subprocess.run(["termux-clipboard-set"], input=text, text=True, check=True)
			return True
		except Exception:
			return False

def add_entry(pwd_manager: PwdManager) -> bool:
	clear_screen()

	website = input("Enter website:\n")
	username = input("Enter username:\n")
	
	print("Generate random password? Y/n")

	key = ''
	while key not in ['y', 'n', 'q']:
		key = get_key()
	
	if key == 'q':
		return False
	if key == 'y':
		password = PwdManager.generate_pwd()
		if safe_copy(password):
			print(f"password = {RED}{password}{RESET} was copied to clipboard")
		else:
			print(f"password = {RED}{password}{RESET}")
	else:
		password = input("Enter password:\n")
	
	description = input("Enter description:\n")

	print(f"Save the following entry? Y/n\n {website = }\n{username = }\n{password = }\n{description = }.")

	while (True):
		ans: str = get_key()

		match ans.lower():
			case "y":
				pwd_manager.add_entry(website, username, password, description)
				return True
			case "n":
				return False

def remove_entry(pwd_manager: PwdManager, entry: Entry) -> bool:
	clear_screen()

	website = entry.get_website()
	username = entry.get_username()

	print(f"Delete entry ({website, username})? Y/n\n")

	ans = get_key()
		
	if ans == "y":
		pwd_manager.remove_entry(website, username)
		return True
	else:
		print("Operation canceled.")
		return False

def get_password(pwd_manager: PwdManager, entry: Entry) -> None:
	clear_screen()

	website = entry.get_website()
	username = entry.get_username()

	pwd = pwd_manager.get_password(website, username)
	print(f"Password: {pwd}")

	if pwd != NO_SUCH_ENTRY_MESSAGE:
		print("Press [c] to copy password to clipboard or [any key] to return to go back.")

		match get_key():
			case 'c':
				if safe_copy(pwd):
					print("Password is copied to clipboard!")
				else:
					print("Could not copy password.")
			case _:
				return

	sleep(1)

def modify_entry(pwd_manager: PwdManager, entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())

	print("Modify [w]ebsite, [u]sername, [p]assword, [d]escription or press [backspace] to go back")

	while True:
		match get_key():
			case 'w':
				return _modify_website(entry)
				break
			case 'u':
				return _modify_username(entry)
				break
			case 'p':
				return _modify_password(pwd_manager, entry)
				break
			case 'd':
				return _modify_description(entry)
				break
			case BACKSPACE:
				return False


def modify_master_password(pwd_manager: PwdManager) -> bool:
	clear_screen()

	print("Enter your new master password or leave empty to go back.\n")
	pwd = input("New Password: ")

	if len(pwd) == 0:
		return False
	else:
		print(f"Change master password to {RED}{pwd}{RESET}? Y/n")

		if get_key() == "y":
			pwd_manager.modify_master_password(pwd)
			return True
		else:
			return False

def save_changes(pwd_manager: PwdManager) -> bool:
	pwd_manager.encrypt()
	return True

def search_entries(pwd_manager: PwdManager) -> bool:
	query = ""
	website_set = set(pwd_manager.get_website_list())
	username_set = set(pwd_manager.get_username_list())

	done = False
	while not done:
		clear_screen()

		print(f"Query: {query}")

		# TODO: Turn this into a real-time filtering function (and move it to its own function)

		# curr_website_set = {website for website in website_set if query in website}
		# curr_username_set = {username for username in username_set if query in username}

		keystroke = get_key()
		query, decrement, done = _handle_keystroke(query, keystroke)
		
		#if decrement:
		#	curr_website_set = {website for website in website_set if query in website}
		#	curr_username_set = {username for username in username_set if query in username}
		#else:
		#	curr_website_set = {website for website in curr_website_set if query in website}
		#	curr_username_set = {username for username in curr_username_set if query in username}
	
	curr_website_set = {website for website in website_set if query in website.lower()}
	curr_username_set = {username for username in username_set if query in username.lower()}

	entries: list[Entry] = []

	for website in curr_website_set:
		entries += pwd_manager.get_entries_by_website(website)
		
	for username in curr_username_set:
		entries += pwd_manager.get_entries_by_username(username)

	#	display logic
	
	index = 0

	while True:
		clear_screen()

		options = display_list([entry.to_string() for entry in entries], index)
		n = len(entries)

		main_str = ""

		if index != 0:
			main_str += "[p] for previous page, "
		if (index + 1) * 10 <= n:
			main_str += "[n] for next page, "
		
		if main_str != "":
			print("Press " + main_str)

		ans = get_key()

		if ans in options:
			i = (10 * index) + int(ans)

			entry = entries[i]

			print(entry.to_string_with_desc())

			return _specific_entry_options(pwd_manager, entry)
		
		match ans:
			case "p":
				if index != 0:
					index -= 1
			case "n":
				if (index + 1) * 10 <= n:
					index += 1
			case "q":
				return False

"""
	puts together the query one keystroke at a time.
	returns (query, decrement, done), where
		- query is the current composed query
		- decrement indicates if the query has gotten shorter (for search and efficiency purposes)
		- done indicates if input is done [enter] was pressed
"""
def _handle_keystroke(query: str, keystroke: str) -> tuple[str, bool, bool]:
	if keystroke == ENTER:
		return query, False, True

	if keystroke == BACKSPACE:
		if query == "":
			return query, False, False
		return query[:-1], True, False
	
	if keystroke in CHARS:
		return query + keystroke, False, False

	return query, False, False


def _modify_website(entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new website for this entry or leave empty to go back.\n")

	website = input("New website: ")

	if len(website) == 0:
		return False
	
	entry.set_website(website)

	return True

def _modify_username(entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new username for this entry or leave empty to go back.\n")

	username = input("New username: ")
	
	if len(username) == 0:
		return False
	
	entry.set_username(username)

	return True

def _modify_description(entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new description for this entry or leave empty to go back.\n")

	description = input("New description: ")

	if len(description) == 0:
		return False
	
	entry.set_description(description)

	return True

def _modify_password(pwd_manager: PwdManager, entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new password for this entry or leave empty to go back.\n")

	password = input("New password: ")

	if len(password) == 0:
		return False

	website = entry.get_website()
	username = entry.get_username()

	pwd_manager.set_password(website, username, password)

	return True


def gen_rand_password() -> None:
	clear_screen()

	pwd = PwdManager.generate_pwd()
	if safe_copy(pwd):
		print(f"Your random password {RED}{pwd}{RESET} was copied to clipboard!")
	else:
		print(f"Your random password is {RED}{pwd}{RESET}")

	print("Press any key to continue..")
	
	get_key()
	return

def is_valid_index(key: str, index: int, bound: int) -> bool:
	return key in DIGITS and (10 * index) + int(key) < bound

def display_list(ls: list, index=0):
	if index < 0:
		raise IndexError("Calling display_list with negative index.")

	start_index = 10 * index
	end_index = min(start_index + 10, len(ls))

	options = []

	for i in range(start_index, end_index):
		print(f"[{i - (10 * index)}]:\t{ls[i]}")
		options.append(f'{i - (10 * index)}')

	return options

def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')
	print(HEADER)

def _init(argv: list[str]) -> PwdManager | int:
	if len(argv) < 2 or len(argv) > 4:
		print("Usage: python this_script.py path/to/file.vault (--create)")
		return 1

	path = argv[1]

	if len(argv) == 2:
		if not Path(path).exists():
			print("Vault path is incorrect")
			return 1

		pwd_manager = PwdManager.from_encrypted_file(path)

		if not pwd_manager:
			print("Something went wrong. Exiting..")
			return 1

	else:
		if (Path(path).exists()):
			print("Vault already exists. Overwrite it? Y/n")

			if get_key() == "y":
				print("Permanently delete the given vault? Y/n")
				if get_key() == "y":
					os.remove(Path(path))
				else:
					return 0
			else:
				return 0

		Path(path).touch()

		pwd = getpass("Enter your master password:")
		pwd_manager = PwdManager.pwd_manager_from_pwd(path, pwd)

	return pwd_manager

def _main_loop(pwd_manager: PwdManager):
	index = 0
	modified = False

	while (True):
		clear_screen()

		n = pwd_manager.get_entry_num()
		
		options = display_list(pwd_manager.get_website_and_username_string(), index)

		main_str = ""

		if index != 0:
			main_str += "[p] for previous page, "
		if (index + 1) * 10 <= n:
			main_str += "[n] for next page, "
		
		main_str += "[a] to add entry, [g] to generate a random password, [m] to modify master password, [f] to search entries, [s] to save current changes or [q] to exit"

		print(f"Press {main_str}\n")
		while True:
		
			ans = get_key()

			if ans in options:
				modified |= _sub_loop(pwd_manager, ans, index)
				break
			else:
				match ans:
					case "q":
						if modified:
							pwd_manager.encrypt()
						sys.exit(0)
					case "a":
						modified |= add_entry(pwd_manager)
						break
					case "g":
						gen_rand_password()
						break
					case "m":
						modified |= modify_master_password(pwd_manager)
						break
					case "f":
						modified |= search_entries(pwd_manager)
						break
					case "s":
						modified &= not save_changes(pwd_manager)	# upon success, we reset modified to False
						break
					case "p":
						if index != 0:
							index -= 1
						break
					case "n":
						if (index + 1) * 10 <= n:
							index += 1
						break


def _sub_loop(pwd_manager: PwdManager, key: str, index: int) -> bool:
	clear_screen()

	if not is_valid_index(key, index, pwd_manager.get_entry_num()):
		return False
	
	i = (10 * index) + int(key)

	entry = pwd_manager.get_entry_by_index(i)

	return _specific_entry_options(pwd_manager, entry)

def _specific_entry_options(pwd_manager: PwdManager, entry: Entry) -> bool:
	print(entry.to_string_with_desc())
	print("\nPress [m] to modify, [d] to delete, [r] to retrieve password, [backspace] to go back.")

	key = get_key()

	match key:
		case 'm':
			return modify_entry(pwd_manager, entry)
		case 'd':
			return remove_entry(pwd_manager, entry)
		case 'r':
			get_password(pwd_manager, entry)
			return False				# since we don't modify anything here
		case BACKSPACE:
			return False


if __name__ == "__main__":
	try:
		pwd_manager = _init(sys.argv)

		if not isinstance(pwd_manager, PwdManager):
			sys.exit(pwd_manager)

		sleep(1)

		try:
			_main_loop(pwd_manager)

		except KeyboardInterrupt:
			print("Save before quitting? Y/n")

			try:
				if get_key() == "y":
					pwd_manager.encrypt()
			except KeyboardInterrupt:				# in case CTRL+C is pressed again, we just quit without saving
				pass

			print("Goodbye")
			sys.exit(0)
	
	#	big net to avoid crashing
	except Exception as e:
		print("Something went wrong. Unsaved changes will not be saved.")
		print(f"Exception: {e!r}")
		sys.exit(1)
