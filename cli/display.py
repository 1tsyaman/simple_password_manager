import os
from core.types import config_t

HEADER		= f"{15*"-"} Password Manager {15*"-"}"
FOOTER		= 48*"-"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RESET = "\033[0m"

"""
	Alignment operatios with column size 20:
		f"{value:<20}"   # left aligned
		f"{value:>20}"   # right aligned
		f"{value:^20}"   # centered
"""

"""
	- displays a list with up to 10 options
	- index represents 'page number' and is used to calculate which options to show
	@returns list of available options (between 0 and 9)
"""
def display_list(ls: list, index=0) -> list[str]:
	options, output = display_list_str(ls, index)
	print(output)
	return options

def display_list_str(ls: list, index=0) -> tuple[list[str], str]:
	if index < 0:
		raise IndexError("Calling display_list with negative index.")

	output = ""
	start_index = 10 * index
	end_index = min(start_index + 10, len(ls))

	options = []

	for i in range(start_index, end_index):
		output += f"[{i - (10 * index)}]:\t{ls[i]}\n"
		options.append(f'{i - (10 * index)}')

	if len(output) != 0:
		output = output[:-1]
	return options, output

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


def clear_screen(header=True):
	os.system('cls' if os.name == 'nt' else 'clear')
	if header:
		print(HEADER)

def print_footer():
	print(FOOTER)

"""
	Expects dicts of the following shape:
		pwd_gen: 
		{
			"special_chars": "!\"#$%&'()*+,-./:<=>?@[\\]^_`{|}~",
			"password_length": 24,
			"use_uppercase": true,
			"use_digits": true,
			"use_special": true
		}
		security:
		{
			"timeout_duration": 60,
		}
"""
def print_settings(
	pwd_gen:	dict[str, config_t],
	security:	dict[str, config_t]
):
	string = ""
	string += f"{'Special Characters:':<32}{pwd_gen['special_chars']}\n"
	string += f"{'Password Length:':<32}{pwd_gen['password_length']}\n"
	string += f"{'Use Uppercase:':<32}{pwd_gen['use_uppercase']}\n"
	string += f"{'Use Digits:':<32}{pwd_gen['use_digits']}\n"
	string += f"{'Use Special Characters:':<32}{pwd_gen['use_special']}\n"
	string += f"{'Inactivity Timeout Duration:':<32}{security['timeout_duration']}\n"

	print(string)

def display_password_rejection_reason(reason: str, min_len: int):
	message = ''
	match reason:
		case 'len':
			message = f'be at least {min_len} characters long'
		case 'digit':
			message = f"contain at least one digit"
		case 'lower':
			message = f"contain at least one lower case letter"
		case 'upper':
			message = f"contain at least one upper case letter"
		case 'special':
			message = f"contain at least one special character"