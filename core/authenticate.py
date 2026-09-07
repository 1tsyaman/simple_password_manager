import hmac
import hashlib
import json

def generate_tag(
	data	: bytes,
	key		: bytes
) -> bytes:
	return hmac.new(
		key,
		data,
		hashlib.sha256
	).digest()

def is_authentic(
	data	: bytes,
	key		: bytes,
	tag		: bytes
) -> bool:
	expected_tag = hmac.new(
		key,
		data,
		hashlib.sha256
	).digest()

	return hmac.compare_digest(tag, expected_tag)

def encode_data(data: dict) -> bytes:
	return json.dumps(
		data,
		sort_keys=True,
		separators=(",", ":")
	).encode()