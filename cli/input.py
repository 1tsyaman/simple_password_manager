import os
import sys
import subprocess

from pyperclip import copy, PyperclipException
from getpass import getpass

from core.pwd_manager import DIGITS, LETTERS_LOWER, SPECIAL_CHARS
from cli.watchdog import reset_on_call

CTRL_C		= ['\x03']
ENTER		= ['\r']
BACKSPACE	= ['\x08', '\x7f']


CHARS = DIGITS + LETTERS_LOWER + SPECIAL_CHARS


"""
	This function is os-specific
	decorator resets watchdog timer on activity
"""
@reset_on_call
def get_key(lower=True) -> str:
	if os.name == "nt":					# if os is windows
		import msvcrt

		key = msvcrt.getch().decode("utf-8")

		if lower:
			key = key.lower()

		if is_ctrl_c(key):
			raise KeyboardInterrupt

		return key
								# otherwise (posix)
	import termios
	from tty import setraw

	fd = sys.stdin.fileno()
	old_settings = termios.tcgetattr(fd)

	try:
		setraw(fd)
		key =  sys.stdin.read(1)

		if lower:
			key = key.lower()

		if is_ctrl_c(key):
			raise KeyboardInterrupt

		return key
	finally:
		termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		
def is_backspace(key: str) -> bool:
	return key in BACKSPACE

def is_enter(key: str) -> bool:
	return key in ENTER

def is_ctrl_c(key: str) -> bool:
	return key in CTRL_C

"""
	- puts together the query one keystroke at a time.
	@returns (query, decrement, done), where
		- query is the current composed query
		- decrement indicates if the query has gotten shorter (for search and efficiency purposes)
		- done indicates if input is done [enter] was pressed
"""
@reset_on_call
def _handle_keystroke(query: str, keystroke: str) -> tuple[str, bool, bool]:
	if is_enter(keystroke):
		return query, False, True

	if is_backspace(keystroke):
		if query == "":
			return query, False, False

		return query[:-1], True, False
	
	if keystroke.lower() in CHARS or keystroke == " ":
		return query + keystroke, False, False

	return query, False, False

def poll_y_n_backspace() -> str:
	key = ''

	while not (key in ['y', 'n'] or is_backspace(key)):
		key = get_key()
	
	return key

def poll_for_with_backspace(ls: list[str]) -> str:
	key = ''

	while not (key in ls or is_backspace(key)):
		key = get_key()
	
	return key

"""
	supports copying mechanism windows, linux (at least ubuntu) and Termux
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

"""
	input() wrapper to enable watchdog reset decoration
"""
@reset_on_call
def get_input(message: str) -> str:
	return input(message)


"""
	getpass wrapper to enable watchdog reset decoration
"""
@reset_on_call
def input_password(message: str) -> str:
	return getpass(message)