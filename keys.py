import os
from argon2.low_level import hash_secret_raw, Type

KEY_LEN			= 32		# 32 bytes = 256-bit AES key
SALT_LEN		= 16		# 16 random bytes is a good salt size

ARGON2_TIME_COST	= 3
ARGON2_MEMORY_COST	= 64 * 1024	# 64 MiB, value is in KiB
ARGON2_PARALLELISM	= 1

def derrive_key(pwd: str, salt=bytes(0)) -> tuple[bytes,bytes]:
	if len(salt) == 0:
		salt = os.urandom(SALT_LEN)
	return salt, hash_secret_raw(
		secret=pwd.encode("utf-8"),
		salt=salt,
		time_cost=ARGON2_TIME_COST,
		memory_cost=ARGON2_MEMORY_COST,
		parallelism=ARGON2_PARALLELISM,
		hash_len=KEY_LEN,
		type=Type.ID,			# Argon2id
	)