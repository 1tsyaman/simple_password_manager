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
	ans = []
	query = query.lower()

	#	filter descriptions
	ans += [entry for entry in ls if query in entry.get_description().lower()]

	ls = list_diff(ls, ans)		# remove added elements from the list to avoid duplications

	#	filter website
	ans += [entry for entry in ls if query in entry.get_website().lower()]

	ls = list_diff(ls, ans)

	#	filter username
	ans += [entry for entry in ls if query in entry.get_username().lower()]

	return ans

def list_diff(ls1: list, ls2: list) -> list:
	return [element for element in ls1 if element not in ls2]