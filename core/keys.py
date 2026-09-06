import os
from argon2.low_level import hash_secret_raw, Type
from argon2.exceptions import HashingError

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from core.errors import KeyDerivationError
from core.constants import (
	KEY_LEN,
	SALT_LEN,
	ARGON2_TIME_COST,
	ARGON2_MEMORY_COST,
	ARGON2_PARALLELISM
)

"""
	Uses expensive Argon2 to derive a master key from
		a password and a salt

	@raises:
		- OSError
		- KeyDerivationError
"""
def derive_master_key(
	pwd: str,
	salt: bytes = bytes(0)
) -> tuple[bytes,bytes]:
	if len(salt) == 0:
		salt = os.urandom(SALT_LEN)

	try:
		secret = pwd.encode("utf-8")
		key = hash_secret_raw(
			secret=secret,
			salt=salt,
			time_cost=ARGON2_TIME_COST,
			memory_cost=ARGON2_MEMORY_COST,
			parallelism=ARGON2_PARALLELISM,
			hash_len=KEY_LEN,
			type=Type.ID,			# Argon2id
		)
	except (HashingError, UnicodeEncodeError) as e:
		raise KeyDerivationError from e

	return salt, key

def get_random_salt() -> bytes:
	return os.urandom(SALT_LEN)

def derive_subkey(
	master_key	: bytes,
	purpose		: str
) -> bytes:
	info = purpose.encode("utf-8")

	return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info,
    ).derive(master_key)