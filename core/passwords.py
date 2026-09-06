import random as rand

from core.constants import (
	LETTERS_LOWER,
	LETTERS_UPPER,
	DIGITS,
	SPECIAL_CHARS,
	MIN_PWD_LENGTH,
	PWD_LENGTH
)

def generate_random_password(
	chars			: list[str],
	password_length	: int,
	use_digits		: bool,
	use_uppercase	: bool,
	use_special		: bool
) -> str:
	while True:
		password = ""

		for _ in range(password_length):
			password += rand.choice(chars)

		satisfies, _ = password_satisfies_explicit_conditions(
			password=password,
			password_length=password_length,
			use_digits=use_digits,
			use_uppercase=use_uppercase,
			use_special=use_special
		)

		if satisfies:
			break

	return password

def password_satisfies_explicit_conditions(
	password		: str,
	password_length	: int		= MIN_PWD_LENGTH,
	use_digits		: bool		= True,
	use_uppercase 	: bool		= True,
	use_special		: bool		= True,
	special_chars	: list[str]	= SPECIAL_CHARS,
) -> tuple[bool, str]:
	if len(password) < password_length:
		return False, f'must be at least {password_length} characters long'

	if use_digits:
		for digit in DIGITS:
			if digit in password:
				break
		else:
			return False, 'must contain at least one digit'

	for letter in LETTERS_LOWER:
		if letter in password:
			break
	else:
		return False, 'must contain at least one lowercase character'

	if use_uppercase:
		for letter in LETTERS_UPPER:
			if letter in password:
				break
		else:
			return False, 'must contain at least one uppercase character'

	if use_special:
		for spec in special_chars:
			if spec in password:
				break
		else:
			return False, 'must contain at least one special character'

	return True, ''