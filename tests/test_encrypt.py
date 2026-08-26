import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.encrypt import (
    ASSOCIATED_DATA,
    CIPHERTEXT,
    NONCE,
    SALT,
    decrypt_data,
    encrypt_data,
    get_key_from_pwd,
)
from core.errors import CorruptedVaultError, KeyLengthError, VaultFormatError
from core.keys import KEY_LEN, SALT_LEN


class EncryptTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * KEY_LEN
        self.salt = b"s" * SALT_LEN

    def test_encrypt_and_decrypt_round_trip(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()

            data = {"github.com, yaman, personal": {"pwd": "secret", "totp_uri": ""}}
            encrypt_data(data, self.key, self.salt, str(path), "metadata")

            self.assertEqual(decrypt_data(self.key, str(path)), data)

    def test_encrypt_writes_expected_record_shape(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()

            encrypt_data({"value": 1}, self.key, self.salt, str(path), "")

            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(record), {SALT, NONCE, CIPHERTEXT, ASSOCIATED_DATA})
            self.assertEqual(bytes.fromhex(record[SALT]), self.salt)
            self.assertEqual(bytes.fromhex(record[ASSOCIATED_DATA]), b"")
            self.assertEqual(len(bytes.fromhex(record[NONCE])), 12)
            self.assertFalse(path.with_name(path.name + ".tmp").exists())

    def test_encrypt_raises_for_missing_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.vault"
            with self.assertRaises(FileNotFoundError):
                encrypt_data({}, self.key, self.salt, str(path), "")

    def test_encrypt_raises_for_invalid_key_length(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()
            with self.assertRaises(KeyLengthError):
                encrypt_data({}, b"short", self.salt, str(path), "")

    def test_decrypt_raises_for_missing_file(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.vault"
            with self.assertRaises(FileNotFoundError):
                decrypt_data(self.key, str(path))

    def test_decrypt_raises_for_invalid_key_length(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()
            with self.assertRaises(KeyLengthError):
                decrypt_data(b"short", str(path))

    def test_decrypt_raises_corrupted_vault_for_wrong_key(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.touch()
            encrypt_data({"secret": "value"}, self.key, self.salt, str(path), "")

            with self.assertRaises(CorruptedVaultError):
                decrypt_data(b"x" * KEY_LEN, str(path))

    def test_decrypt_raises_vault_format_error_for_invalid_json(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.write_text("{not-json", encoding="utf-8")

            with self.assertRaises(VaultFormatError):
                decrypt_data(self.key, str(path))

    def test_decrypt_raises_vault_format_error_for_missing_record_field(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.write_text(
                json.dumps({
                    SALT: self.salt.hex(),
                    NONCE: "00" * 12,
                    CIPHERTEXT: "",
                }),
                encoding="utf-8",
            )

            with self.assertRaises(VaultFormatError):
                decrypt_data(self.key, str(path))

    def test_get_key_from_pwd_uses_stored_salt(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.write_text(
                json.dumps({
                    SALT: self.salt.hex(),
                    NONCE: "00" * 12,
                    CIPHERTEXT: "",
                    ASSOCIATED_DATA: "",
                }),
                encoding="utf-8",
            )

            derived_key = b"d" * KEY_LEN
            with patch("core.encrypt.derive_key", return_value=(self.salt, derived_key)) as derive:
                result = get_key_from_pwd("Master1!", str(path))

            self.assertEqual(result, (self.salt, derived_key))
            derive.assert_called_once_with("Master1!", self.salt)

    def test_get_key_from_pwd_rejects_invalid_salt(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "vault.vault"
            path.write_text(
                json.dumps({
                    SALT: "00",
                    NONCE: "00" * 12,
                    CIPHERTEXT: "",
                    ASSOCIATED_DATA: "",
                }),
                encoding="utf-8",
            )

            with self.assertRaises(VaultFormatError):
                get_key_from_pwd("Master1!", str(path))


if __name__ == "__main__":
    unittest.main()
