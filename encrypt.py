from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pathlib import Path
import json
import os

RECORD_KEYS = ["nonce", "ciphertext", "associated_data"]

def encrypt_data(data: dict, key: bytes, file_path: str, associated_data: str) -> None:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)

	if len(key) != 32:
		raise ValueError("AES-256 key must be exactly 32 bytes")

	data_bytes = bytes(json.dumps(data), encoding="utf-8")

	ad = bytes(0)

	if associated_data != "":
		ad = bytes(associated_data, encoding="utf-8")
	
	encrypted, nonce = __encrypt_data(data=data_bytes, key=key, associated_data=ad)

	record = {
		"nonce":		nonce.hex(),
		"ciphertext":		encrypted.hex(),
		"associated_data":	ad.hex()
	}

	with open(path, 'w') as fd:
		json.dump(record, fd)


def __encrypt_data(data: bytes, key: bytes, associated_data: bytes | None) -> tuple[bytes, bytes]:
	aesgcm = AESGCM(key)
	nonce = os.urandom(12)

	encrypted = aesgcm.encrypt(data=data, associated_data=associated_data, nonce=nonce)

	return encrypted, nonce


def decrypt_data(key: bytes, file_path: str) -> dict:
	path = Path(file_path)

	if (not path.exists()):
		raise FileNotFoundError(file_path)
	
	if len(key) != 32:
		raise ValueError("AES-256 key must be exactly 32 bytes")
	
	aesgcm = AESGCM(key)
	
	record = {}

	with open(path, 'r') as fd:
		record = json.load(fd)
	
	if not RECORD_KEYS in record.keys():
		raise ValueError(f"Provided file_path {file_path} is not a valid vault file.")

	nonce = bytes.fromhex(record["nonce"])
	encrypted = bytes.fromhex(record["ciphertext"])
	associated_data = bytes.fromhex(record["associated_data"])

	decrypted_data = aesgcm.decrypt(data=encrypted, associated_data=associated_data, nonce=nonce)
	
	#TODO: Should convert the data from bytes to json (same as the original data)

