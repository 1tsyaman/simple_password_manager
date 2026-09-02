import sys
import os
import signal
import traceback
import argparse

from time import sleep
from typing import Never

import cli.actions as act

from core.pwd_manager import PwdManager
from core.entry import Entry
from cli.input import get_key, poll_for_with_backspace
from cli.display import display_list, clear_screen, print_footer
from cli.util import format_prev_next_str, is_valid_index
from storage.io import load_vault, create_and_load_vault, vault_exists, delete_file
from cli.watchdog import init_watchdog, cancel_watchdog, timeout_occurred

from core.errors import (
	KeyLengthError,
	KeyDerivationError,
	PasswordError,
	VaultFormatError,
	CorruptedVaultError,
	PasswordRequirementsError,
	InconsistentVaultState,
)

GENERAL_ERROR	= "Something went wrong. Exiting..."

def _init(argv: list[str]) -> PwdManager | int:
	parser = argparse.ArgumentParser(
		description="Simple Password Manager CLI"
	)
	parser.add_argument(
		"path",
		help="Path to the vault file"
	)
	parser.add_argument(
		"--create",
		action="store_true",		# if argument is present -> parser stores 'True'
		help="Create a new vault"
	)

	args = parser.parse_args(argv[1:])	# ignore the executable name

	init_watchdog(exit_func=timeout_exit)

	path = args.path

	if not args.create:
		pwd = act.grab_master_password()

		try:
			pwd_manager = load_vault(path, pwd)
		except PasswordError:
			print("Vault loading failed: Password incorrect")
			return -1
		except FileNotFoundError as e:
			print(f"Vault loading failed: Vault file path is incorrect: {e}")
			return -1
		except KeyLengthError:
			print("Vault loading failed: Key length is unexpected")
			return -1
		except KeyDerivationError:
			print("Vault loading failed: Could not derive encryption key")
			return -1
		except VaultFormatError:
			print("Vault loading failed: Vault format is unexpected")
			return -1
		except CorruptedVaultError:
			print("Vault loading failed: Incorrect password or corrupted vault")
			return -1
		except InconsistentVaultState:
			print("Vault loading failed, check log")
			return -1
		except OSError as e:
			print(f"Vault loading failed: {e}")
			return -1

	else:
		try:
			path_exists = vault_exists(path)
		except OSError as e:
			print(f"Checking vault path failed: {e}")
			return -1

		if path_exists:
			ans = act.double_check_deletion(message1="Vault already exists. Overwrite it? Y/n",
						message2="Permanently delete the given vault? Y/n")
			if ans:
				try:
					delete_file(path)
				except OSError as e:
					print(f"Deleting vault failed: {e}")
					return -1
			else:
				print("Goodbye.")
				return 0

		pwd = act.grab_master_password(new=True)

		try:
			pwd_manager = create_and_load_vault(path, pwd)
		except KeyLengthError:
			print("Vault creation failed: Key length is unexpected")
			return -1
		except KeyDerivationError:
			print("Vault creation failed: Could not derive encryption key")
			return -1
		except PasswordRequirementsError as e:
			print(f"Vault creation failed: Password does not satisfy the minimum requirements: Reason: {e.reason}")
			return -1
		except OSError as e:
			print(f"Vault creation failed: {e}")
			return -1

	return pwd_manager

def _main_loop(pwd_manager: PwdManager):
	index = 0
	modified = False

	while (True):
		clear_screen()

		n = pwd_manager.get_entry_list_len()
		options = display_list(pwd_manager.get_website_and_username_string_list(), index)
		
		print_footer()

		main_str = ""

		if len(options) > 0:
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
	while True:
		print(entry.get_formatted_entry_string())
		print_footer()

		options = ['m', 'd', 'r', 'BACKSPACE']

		totp_message = ""

		if entry.has_totp():
			totp_message = " [g] to get TOTP code,"
			options += ['g']

		print(f"Press [m] to modify, [d] to delete, [r] to retrieve password,{totp_message} [backspace] to go back.")

		key = poll_for_with_backspace(options)

		match key:
			case 'm':
				return act.modify_entry(pwd_manager, entry)
			case 'd':
				return act.remove_entry(pwd_manager, entry)
			case 'r':
				act.get_password(pwd_manager, entry)
			case 'g':
				act.get_totp_code(pwd_manager, entry)
			case _:
				return False

		clear_screen()
		
def cleanup() -> None:
	clear_screen(header=False)
	cancel_watchdog()

def quit_program(exit_code=0, message='') -> Never:
	cleanup()
	print(message)

	sys.exit(exit_code)

def timeout_exit() -> None:
	os.kill(os.getpid(), signal.SIGINT)		# sends a ctrl+c interrupt to kill the process

def main(argv):
	pwd_manager: PwdManager | int = -1
	try:
		pwd_manager = _init(argv)

		if not isinstance(pwd_manager, PwdManager):	# returns int if it fails
			sleep(2)
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
			if get_key() == "y" and isinstance(pwd_manager, PwdManager):
				pwd_manager.encrypt()
		except KeyboardInterrupt:				# in case CTRL+C is pressed again, we just quit without saving
			pass
		except FileNotFoundError as e:
			print(f"Saving failed: Vault file path is incorrect: {e}")
		except KeyLengthError:
			print(f"Saving failed: Key length is not as expected.")
		except OverflowError:
			print("Saving failed: Vault is too large to encrypt.")
		except OSError as e:
			print(f"Saving failed: {e}")

		quit_program(exit_code=0, message="Goodbye")

	except Exception as e:	# big net to avoid crashing
		message = f"Something went wrong. Unsaved changes will not be saved.\nException: {e!r}"
		cleanup()
		print(message)
		traceback.print_exc()
		sys.exit(-1)

if __name__ == "__main__":
	main(sys.argv)