import os

HEADER		= f"{15*"-"} Password Manager {15*"-"}"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"


"""
	- displays a list with up to 10 options
	- index represents 'page number' and is used to calculate which options to show
	@returns list of available options (between 0 and 9)
"""
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

def str_color(input: str, color: str):
	c = ""

	match color:
		case 'r':
			c = RED
		case 'g':
			c = GREEN
		case 'y':
			c = YELLOW
		case 'b':
			c = BLUE
		case _:
			return input

	return f"{c}{input}{RESET}"


def clear_screen():
	os.system('cls' if os.name == 'nt' else 'clear')
	print(HEADER)