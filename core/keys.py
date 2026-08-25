import os
from argon2.low_level import hash_secret_raw, Type
from argon2.exceptions import HashingError

from core.errors import KeyDerivationError

KEY_LEN				= 32		# 32 bytes = 256-bit AES key
SALT_LEN			= 16		# 16 random bytes is a good salt size

ARGON2_TIME_COST	= 3
ARGON2_MEMORY_COST	= 64 * 1024	# 64 MiB, value is in KiB
ARGON2_PARALLELISM	= 1

"""
	@raises:
		- OSError
		- KeyDerivationError
"""
def derive_key(
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