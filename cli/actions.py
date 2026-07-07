from time import sleep
from core.pwd_manager import PwdManager, NO_SUCH_ENTRY_MESSAGE
from core.entry import Entry
from cli.input import safe_copy, get_key, poll_y_n_backspace, poll_for_with_backspace, is_backspace, _handle_keystroke
from cli.display import clear_screen, display_list, display_list_str, str_color
from cli.util import filter_list, list_diff, format_prev_next_str

def add_entry(pwd_manager: PwdManager) -> bool:
	clear_screen()

	website = input("Enter website: ")
	username = input("Enter username: ")
	
	print("Generate random password? Y/n")

	key = get_key()

	if key == 'y':
		password = PwdManager.generate_pwd()

		if safe_copy(password):
			print(f"password = {str_color(password, 'r')} was copied to clipboard")
		else:
			print(f"password = {str_color(password, 'r')}")

	else:
		password = input("Enter password: ")

	description = input("Enter description: ")

	print(f"Save the following entry? Y/n\n {website = }\n{username = }\n{password = }\n{description = }.")

	ans = poll_y_n_backspace()

	if ans == 'y':
		pwd_manager.add_entry(website, username, password, description)
		return True
	
	return False

def remove_entry(pwd_manager: PwdManager, entry: Entry) -> bool:
	clear_screen()

	website = entry.get_website()
	username = entry.get_username()

	print(f"Delete entry ({website, username})? Y/n")

	ans = poll_y_n_backspace()

	if ans == "y":
		pwd_manager.remove_entry(website, username)
		return True

	print("Operation canceled.")
	return False

def get_password(pwd_manager: PwdManager, entry: Entry) -> None:
	clear_screen()

	website = entry.get_website()
	username = entry.get_username()

	pwd = pwd_manager.get_password(website, username)

	if pwd == NO_SUCH_ENTRY_MESSAGE:
		return print(NO_SUCH_ENTRY_MESSAGE)

	print(f"Website: {website}\nUsername: {username}\nPassword: {pwd}")

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
	while True:
		clear_screen()

		modified = False

		print(entry.to_string_with_desc())

		print("Modify [w]ebsite, [u]sername, [p]assword, [d]escription or press [backspace] to go back")

		while True:
			key = get_key()
			match key:
				case 'w':
					modified |= _modify_website(entry)
					break
				case 'u':
					modified |= _modify_username(entry)
					break
				case 'p':
					modified |= _modify_password(pwd_manager, entry)
					break
				case 'd':
					modified |= _modify_description(entry)
					break
				case _:
					if is_backspace(key):
						return modified


def modify_master_password(pwd_manager: PwdManager) -> bool:
	clear_screen()

	print("Enter your new master password or leave empty to go back.")
	pwd = input("New Password: ")

	if len(pwd) == 0:
		return False
	else:
		print(f"Change master password to {str_color(pwd, 'r')}? Y/n")

		key = poll_y_n_backspace()

		if key == "y":
			pwd_manager.modify_master_password(pwd)
			
			print("Master password updated successfully,")

			sleep(1)
			return True

		return False

def save_changes(pwd_manager: PwdManager) -> bool:
	print("Changes saved.")
	sleep(1)
	pwd_manager.encrypt()
	return True

def handle_query(pwd_manager: PwdManager) -> list[Entry]:
	query = ""
	done = False

	original_list = pwd_manager.get_entry_list()
	ans = original_list

	clear_screen()

	while not done:
		clear_screen()

		print(f"Query: {query}")
		_, output = display_list_str([entry.to_string() for entry in ans])	# only shows the first 10 matches
		print("\n"+ f"{40*"-"}\n" + output)

		keystroke = get_key()
	
		query, decrement, done = _handle_keystroke(query, keystroke)

		if decrement:
			ans = filter_list(original_list, query)
		else:
			ans = filter_list(ans, query)
	
	return ans

def search_entries(pwd_manager: PwdManager) -> Entry | None:
	candidates = handle_query(pwd_manager)
	
	if len(candidates) == 0:
		return None

	index = 0

	while True:
		clear_screen()

		n = len(candidates)
		options = display_list([entry.to_string() for entry in candidates], index)

		main_str = format_prev_next_str(index, len=n)
		
		if len(main_str) != 0:
			print(f"Press {main_str}")

		ans = poll_for_with_backspace(options + ['p', 'n'])

		if ans in options:
			i = (10 * index) + int(ans)

			entry = candidates[i]

			print(entry.to_string_with_desc())

			return entry
		
		match ans:
			case "p":
				if index != 0:
					index -= 1
			case "n":
				if (index + 1) * 10 <= n:
					index += 1
			case _:
				return None


def _modify_website(entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new website for this entry or leave empty to go back.")

	website = input("New website: ")

	if len(website) == 0:
		return False
	
	entry.set_website(website)

	return True

def _modify_username(entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new username for this entry or leave empty to go back.")

	username = input("New username: ")
	
	if len(username) == 0:
		return False
	
	entry.set_username(username)

	return True

def _modify_description(entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new description for this entry or leave empty to go back.")

	description = input("New description: ")

	if len(description) == 0:
		return False
	
	entry.set_description(description)

	return True

def _modify_password(pwd_manager: PwdManager, entry: Entry) -> bool:
	clear_screen()

	print(entry.to_string_with_desc())
	print("Input new password for this entry or leave empty to go back.")

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
		print(f"Your random password {str_color(pwd, 'r')} was copied to clipboard!")
	else:
		print(f"Your random password is {str_color(pwd, 'r')}")

	print("Press any key to continue..")
	
	get_key()
	return


def double_check_deletion(message1: str, message2: str) -> bool:
	print(message1)
	if get_key() == "y":
		print(message2)
		if get_key() == "y":
			return True
		else:
			return False
	else:
		return False