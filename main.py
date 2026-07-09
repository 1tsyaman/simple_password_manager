import sys
import os
import signal

from time import sleep

import cli.actions as act

from core.pwd_manager import PwdManager
from core.entry import Entry
from cli.input import get_key, poll_for_with_backspace
from cli.display import display_list, clear_screen, print_footer, display_password_rejection_reason
from cli.util import format_prev_next_str, is_valid_index
from storage.io import load_vault, create_and_load_vault, vault_exists, delete_vault
from cli.watchdog import init_watchdog, cancel_watchdog, timeout_occurred

GENERAL_ERROR	= "Something went wrong. Exiting..."

def _init(argv: list[str]) -> PwdManager | int:
	if len(argv) < 2 or len(argv) > 4:
		print("Usage: python this_script.py path/to/file.vault (--create)")
		return 1

	init_watchdog(exit_func=timeout_exit)

	path = argv[1]

	if len(argv) == 2:
		pwd = act.grab_master_password()
		pwd_manager = load_vault(path, pwd)
	
		if not pwd_manager:
			print(GENERAL_ERROR)
			return -1

	else:
		if (vault_exists(path)):
			ans = act.double_check_deletion(message1="Vault already exists. Overwrite it? Y/n",
						message2="Permanently delete the given vault? Y/n")
			if ans:
				delete_vault(path)
			else:
				print("Goodbye.")
				return 0

		pwd = act.grab_master_password(new=True)
		pwd_manager = create_and_load_vault(path, pwd)

		if not pwd_manager:
			print(GENERAL_ERROR)
			return -1

	return pwd_manager

def _main_loop(pwd_manager: PwdManager):
	index = 0
	modified = False

	while (True):
		clear_screen()

		n = pwd_manager.get_entry_list_len()
		options = display_list(pwd_manager.get_website_and_username_string(), index)
		
		print_footer()
		actual_index = 10 * index + 1
		print(f"Showing entries {actual_index}..{actual_index + int(options[-1])} out of {n}")
		main_str = format_prev_next_str(index, len=n)
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
						if modified and pwd_manager is not None:
							act.save_changes(pwd_manager)
							sleep(1)
						return
					case "a":
						modified |= act.add_entry(pwd_manager)
						break
					case "g":
						act.gen_rand_password()
						break
					case "m":
						modified |= act.modify_master_password(pwd_manager)
						break
					case "f":
						entry = act.search_entries(pwd_manager)
						if entry is not None:
							clear_screen()
							modified |= _specific_entry_options(pwd_manager, entry)
						break
					case "s":
						modified &= not act.save_changes(pwd_manager)	# upon success, we reset modified to False
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

	if not is_valid_index(key, index, pwd_manager.get_entry_list_len()):
		return False
	
	i = (10 * index) + int(key)

	entry = pwd_manager.get_entry_by_index(i)

	return _specific_entry_options(pwd_manager, entry)

def _specific_entry_options(pwd_manager: PwdManager, entry: Entry) -> bool:
	print(entry.to_string_with_desc())
	print_footer()
	print("Press [m] to modify, [d] to delete, [r] to retrieve password, [backspace] to go back.")

	key = poll_for_with_backspace(['m', 'd', 'r', 'BACKSPACE'])

	match key:
		case 'm':
			return act.modify_entry(pwd_manager, entry)
		case 'd':
			return act.remove_entry(pwd_manager, entry)
		case 'r':
			act.get_password(pwd_manager, entry)
			return False				# since we don't modify anything here
		case _:
			return False
		
def cleanup() -> None:
	clear_screen(header=False)
	cancel_watchdog()

def quit_program(exit_code=0, message='') -> None:
	cleanup()
	print(message)

	sys.exit(exit_code)

def timeout_exit() -> None:
	os.kill(os.getpid(), signal.SIGINT)		# sends a ctrl+c interrupt to kill the 

if __name__ == "__main__":
	try:
		pwd_manager = _init(sys.argv)

		if not isinstance(pwd_manager, PwdManager):	# returns int if it fails
			quit_program(exit_code=pwd_manager, message="Failed to initalize PwdManager object.")

		sleep(1)	# show success before clearing the screen

		_main_loop(pwd_manager)
		quit_program(exit_code=0, message="Goodbye")

	except KeyboardInterrupt:				# this covers two cases: timeout, or ctrl+c input by user
		if timeout_occurred():
			message = "Inactive for too long. Exisitng without saving."
			quit_program(exit_code=0, message=message)

		# otherwise -> user interrupt.
		clear_screen(header=False)
		print("Save before quitting? Y/n")

		try:
			if get_key() == "y":
				pwd_manager.encrypt()
		except KeyboardInterrupt:				# in case CTRL+C is pressed again, we just quit without saving
			pass

		quit_program(exit_code=0, message="Goodbye")

	except Exception as e:	#	big net to avoid crashing
		clear_screen(header=False)
		message = f"Something went wrong. Unsaved changes will not be saved.\nException: {e!r}"
		quit_program(exit_code=-1, message=message)
