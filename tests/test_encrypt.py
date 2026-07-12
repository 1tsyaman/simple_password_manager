import json
import tempfile
import unittest
from pathlib import Path

from core.encrypt import (
    ASSOCIATED_DATA,
    CIPHERTEXT,
    NONCE,
    RECORD_KEYS,
    SALT,
    decrypt_data,
    encrypt_data,
    get_key_from_pwd,
)
from core.keys import KEY_LEN, derrive_key
from tests.helpers import VALID_MASTER_PASSWORD


class EncryptionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "vault.json"
        self.path.touch()
        self.salt, self.key = derrive_key(VALID_MASTER_PASSWORD)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_encrypt_decrypt_round_trip(self):
        data = {"example.com, user, note": {"pwd": "secret"}}
        encrypt_data(data, self.key, self.salt, str(self.path), "")
        self.assertEqual(decrypt_data(self.key, str(self.path)), data)

    def test_record_contains_only_expected_fields(self):
        encrypt_data({}, self.key, self.salt, str(self.path), "metadata")
        record = json.loads(self.path.read_text())
        self.assertEqual(set(record), set(RECORD_KEYS))
        self.assertEqual(record[SALT], self.salt.hex())
        self.assertEqual(bytes.fromhex(record[ASSOCIATED_DATA]), b"metadata")

    def test_new_nonce_is_generated_for_every_write(self):
        encrypt_data({"a": 1}, self.key, self.salt, str(self.path), "")
        nonce_1 = json.loads(self.path.read_text())[NONCE]
        encrypt_data({"a": 1}, self.key, self.salt, str(self.path), "")
        nonce_2 = json.loads(self.path.read_text())[NONCE]
        self.assertNotEqual(nonce_1, nonce_2)

    def test_wrong_key_cannot_decrypt(self):
        encrypt_data({"a": 1}, self.key, self.salt, str(self.path), "")
        _, wrong_key = derrive_key("DifferentPassword1!", self.salt)
        with self.assertRaises(KeyError):
            decrypt_data(wrong_key, str(self.path))

    def test_tampered_ciphertext_is_rejected(self):
        encrypt_data({"a": 1}, self.key, self.salt, str(self.path), "")
        record = json.loads(self.path.read_text())
        ciphertext = bytearray.fromhex(record[CIPHERTEXT])
        ciphertext[0] ^= 1
        record[CIPHERTEXT] = ciphertext.hex()
        self.path.write_text(json.dumps(record))
        with self.assertRaises(KeyError):
            decrypt_data(self.key, str(self.path))

    def test_get_key_from_password_uses_stored_salt(self):
        encrypt_data({}, self.key, self.salt, str(self.path), "")
        returned_salt, returned_key = get_key_from_pwd(VALID_MASTER_PASSWORD, str(self.path))
        self.assertEqual(returned_salt, self.salt)
        self.assertEqual(returned_key, self.key)

    def test_encrypt_rejects_missing_file(self):
        missing = self.path.with_name("missing.vault")
        with self.assertRaises(FileNotFoundError):
            encrypt_data({}, self.key, self.salt, str(missing), "")

    def test_decrypt_rejects_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            decrypt_data(self.key, str(self.path.with_name("missing.vault")))

    def test_encrypt_rejects_wrong_key_length(self):
        with self.assertRaises(KeyError):
            encrypt_data({}, b"x" * (KEY_LEN - 1), self.salt, str(self.path), "")

    def test_decrypt_rejects_wrong_key_length(self):
        with self.assertRaises(KeyError):
            decrypt_data(b"x" * (KEY_LEN - 1), str(self.path))

    def test_missing_record_field_is_rejected(self):
        self.path.write_text(json.dumps({NONCE: "", CIPHERTEXT: "", ASSOCIATED_DATA: ""}))
        with self.assertRaises(ValueError):
            get_key_from_pwd(VALID_MASTER_PASSWORD, str(self.path))

    def test_atomic_write_leaves_no_temporary_file(self):
        encrypt_data({"a": 1}, self.key, self.salt, str(self.path), "")
        self.assertFalse(self.path.with_name(self.path.name + ".tmp").exists())
