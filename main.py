import sys
import os
from pathlib import Path
from getpass import getpass

from pwd_manager import PwdManager
 

def add_entry(pwd_manager: PwdManager) -> None:
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
		website = input("Enter website:\n")
		username = input("Enter username:\n")

		print(pwd_manager.get_password(website, username))

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
			print("Vault already exists")
			sys.exit(1)

		Path.touch(Path(path))

		pwd = getpass("Enter your master password:")
		pwd_manager = PwdManager.pwd_manager_from_pwd(path, pwd)

	while (True):
		ans = input("Enter 1 to add entry, 2 to remove entry, 3 to retrieve password or 'quit' to exit\n")
		match ans:
			case "quit":
				pwd_manager.encrypt_and_exit()
				sys.exit(1)
			case "1":
				add_entry(pwd_manager)
			case "2":
				remove_entry(pwd_manager)
			case "3":
				get_password(pwd_manager)
			case _:
				print("Incorrect choice.")
