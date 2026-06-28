import json
import os

from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


from keys import derrive_key, KEY_LEN

NONCE		= "nonce"
CIPHERTEXT	= "ciphertext"
ASSOCIATED_DATA	= "associated_data"
SALT		= "salt"

RECORD_KEYS = [NONCE, CIPHERTEXT, ASSOCIATED_DATA, SALT]

def encrypt_data(data: dict, key: bytes, salt: bytes, file_path: str, associated_data: str) -> None:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)

	if len(key) != KEY_LEN:
		raise KeyError("Something went wrong: Key is not of the expected length.")

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


def get_key_from_pwd(pwd: str, file_path: str) -> tuple[bytes, bytes]:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)

	record = {}

	with open(path, 'r') as fd:
		record = json.load(fd)

	for dict_key in RECORD_KEYS:
		if not dict_key in record.keys():
			raise ValueError(f"Provided file_path {file_path} is not a valid vault file.")

	return derrive_key(pwd, bytes.fromhex(record[SALT]))


def decrypt_data(key: bytes, file_path: str) -> dict:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)
	
	if len(key) != KEY_LEN:
		raise KeyError("Something went wrong: Key is not of the expected length.")

	record = {}

	with open(path, 'r') as fd:
		record = json.load(fd)

	for dict_key in RECORD_KEYS:
		if not dict_key in record.keys():
			raise ValueError(f"Provided file_path {file_path} is not a valid vault file.")

	return __decrypt_data(key, record)


def __decrypt_data(key: bytes, record: dict) -> dict:
	aesgcm = AESGCM(key)

	nonce = bytes.fromhex(record[NONCE])
	encrypted = bytes.fromhex(record[CIPHERTEXT])
	associated_data = bytes.fromhex(record[ASSOCIATED_DATA])
	
	try:
		decrypted_data = aesgcm.decrypt(data=encrypted, associated_data=associated_data, nonce=nonce)
	except InvalidTag:
		raise KeyError("Something went wrong: Ciphertext has been changed, or key/nonce/associated data are wrong.")

	data = json.loads(decrypted_data.decode("utf-8"))

	return data


def __atomic_write(data: dict, path: Path):
	tmp_path = path.with_name(path.name + ".tmp")
	with open(tmp_path, 'w', encoding="utf-8") as fd:
		json.dump(data, fd)

		fd.flush()			# force python to actually pass buffer to os
		os.fsync(fd.fileno())		# sync makes os carry out the write operation to disk
	
	os.replace(tmp_path, path)		# override old file only if write is successful (atomic write)