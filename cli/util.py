from core.pwd_manager import DIGITS
from core.entry import Entry

def is_valid_index(key: str, index: int, bound: int) -> bool:
	return key in DIGITS and (10 * index) + int(key) < bound

def format_prev_next_str(index: int, len: int) -> str:
	main_str = ""

	if index != 0:
			main_str += "[p] for previous page, "
	if (index + 1) * 10 <= len:
		main_str += "[n] for next page, "
		
	return main_str

def filter_list(ls: list[Entry], query: str) -> list[Entry]:
	keywords = query.lower().split()

	return [
		entry for entry in ls 
		if all(
			any(
				keyword in value.lower()
				for value in (
					entry.get_description(),
					entry.get_website(),
					entry.get_username()
				)
			)
			for keyword in keywords
		)
	]

def list_diff(ls1: list, ls2: list) -> list:
	return [element for element in ls1 if element not in ls2]