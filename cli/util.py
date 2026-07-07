from core.pwd_manager import DIGITS

def is_valid_index(key: str, index: int, bound: int) -> bool:
	return key in DIGITS and (10 * index) + int(key) < bound

def format_main_str(index: int, len: int) -> str:
	main_str = ""

	if index != 0:
			main_str += "[p] for previous page, "
	if (index + 1) * 10 <= len:
		main_str += "[n] for next page, "
		
	main_str += "[a] to add entry, [g] to generate a random password, [m] to modify master password, [f] to search entries, [s] to save current changes or [q] to exit"
	
	return main_str