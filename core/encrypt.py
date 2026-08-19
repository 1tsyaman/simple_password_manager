import json
import os

from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


from core.keys import derrive_key, KEY_LEN, SALT_LEN
from core.errors import KeyLengthError, VaultFormatError, CorruptedVaultError

NONCE		= "nonce"
CIPHERTEXT	= "ciphertext"
ASSOCIATED_DATA	= "associated_data"
SALT		= "salt"

RECORD_KEYS = [NONCE, CIPHERTEXT, ASSOCIATED_DATA, SALT]

"""
	@raises:
		- FileNotFoundError(path) [OSError]
		- KeyLengthError
		- OverflowError
		- OSError
"""
def encrypt_data(data: dict, key: bytes, salt: bytes, file_path: str, associated_data: str) -> None:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)

	if len(key) != KEY_LEN:
		raise KeyLengthError

	data_bytes = bytes(json.dumps(data), encoding="utf-8")

	ad = bytes(0)

	if associated_data != "":
		ad = bytes(associated_data, encoding="utf-8")

	encrypted, nonce = __encrypt_data(data=data_bytes, key=key, associated_data=ad)

	record = {
		SALT:			salt.hex(),
		NONCE:			nonce.hex(),
		CIPHERTEXT:		encrypted.hex(),
		ASSOCIATED_DATA:	ad.hex()
	}

	__atomic_write(record, path)


def __encrypt_data(data: bytes, key: bytes, associated_data: bytes | None) -> tuple[bytes, bytes]:
	aesgcm = AESGCM(key)
	nonce = os.urandom(12)

	encrypted = aesgcm.encrypt(data=data, associated_data=associated_data, nonce=nonce)

	return encrypted, nonce


"""
	@raises:
		- FileNotFoundError(path) [OSError]
		- VaultFormatError
		- KeyDerivationError
		- OSError
"""
def get_key_from_pwd(pwd: str, file_path: str) -> tuple[bytes, bytes]:
	path = Path(file_path)

	if not path.exists():
		raise FileNotFoundError(file_path)

	try:
		with open(path, 'r', encoding="utf-8") as fd:
			record = json.load(fd)
	except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as e:
		raise VaultFormatError from e

	if not isinstance(record, dict):
		raise VaultFormatError

	if any(dict_key not in record for dict_key in RECORD_KEYS):
		raise VaultFormatError

	if any(not isinstance(record[dict_key], str) for dict_key in RECORD_KEYS):
		raise VaultFormatError

	try:
		salt = bytes.fromhex(record[SALT])
	except ValueError as e:
		raise VaultFormatError from e

	if len(salt) != SALT_LEN:
		raise VaultFormatError

	return derrive_key(pwd, salt)

"""
	@raises:
		- FileNotFoundError(path) [OSError]
		- KeyLengthError
		- VaultFormatError
		- CorruptedVaultError
		- OSError
"""
def decrypt_data(key: bytes, file_path: str) -> dict:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)
	
	if len(key) != KEY_LEN:
		raise KeyLengthError

	try:
		with open(path, 'r', encoding="utf-8") as fd:
			record = json.load(fd)
	except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as e:
		raise VaultFormatError from e

	if not isinstance(record, dict):
		raise VaultFormatError

	if any(dict_key not in record for dict_key in RECORD_KEYS):
		raise VaultFormatError

	if any(not isinstance(record[dict_key], str) for dict_key in RECORD_KEYS):
		raise VaultFormatError

	return __decrypt_data(key, record)


"""
	@raises:
		- CorruptedVaultError
		- VaultFormatError
"""
def __decrypt_data(key: bytes, record: dict) -> dict:
	aesgcm = AESGCM(key)

	try:
		nonce = bytes.fromhex(record[NONCE])
		encrypted = bytes.fromhex(record[CIPHERTEXT])
		associated_data = bytes.fromhex(record[ASSOCIATED_DATA])
	except (TypeError, ValueError) as e:
		raise VaultFormatError from e

	try:
		decrypted_data = aesgcm.decrypt(data=encrypted, associated_data=associated_data, nonce=nonce)
	except InvalidTag as e:
		raise CorruptedVaultError from e
	except ValueError as e:
		raise VaultFormatError from e

	try:
		data = json.loads(decrypted_data.decode("utf-8"))
	except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as e:
		raise VaultFormatError from e

	return data

"""
	@raises:
		- OSError
"""
def __atomic_write(data: dict, path: Path):
	tmp_path = path.with_name(path.name + ".tmp")
	with open(tmp_path, 'w', encoding="utf-8") as fd:
		json.dump(data, fd)

		fd.flush()			# force python to actually pass buffer to os
		os.fsync(fd.fileno())		# sync makes os carry out the write operation to disk
	
	os.replace(tmp_path, path)		# override old file only if write is successful (atomic write)