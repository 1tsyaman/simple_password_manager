import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encrypt import (
    ASSOCIATED_DATA,
    CIPHERTEXT,
    NONCE,
    SALT,
    decrypt_data,
    encrypt_data,
    get_key_from_pwd,
)
from keys import KEY_LEN, SALT_LEN, derrive_key


class EncryptionTests(unittest.TestCase):
    def test_encrypt_then_decrypt_round_trip(self):
        data = {"github.com, yaman, main account": "secret"}
        key = b"k" * KEY_LEN
        salt = b"s" * SALT_LEN

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.touch()

            encrypt_data(data, key, salt, str(vault), associated_data="vault-v1")
            decrypted = decrypt_data(key, str(vault))

        self.assertEqual(decrypted, data)

    def test_encrypt_writes_expected_record_fields_as_hex_strings(self):
        key = b"k" * KEY_LEN
        salt = b"s" * SALT_LEN

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.touch()

            encrypt_data({"site, user, desc": "secret"}, key, salt, str(vault), associated_data="ad")
            record = json.loads(vault.read_text(encoding="utf-8"))

        self.assertEqual(set(record), {SALT, NONCE, CIPHERTEXT, ASSOCIATED_DATA})
        self.assertEqual(bytes.fromhex(record[SALT]), salt)
        self.assertEqual(bytes.fromhex(record[ASSOCIATED_DATA]), b"ad")
        self.assertEqual(len(bytes.fromhex(record[NONCE])), 12)
        self.assertGreater(len(bytes.fromhex(record[CIPHERTEXT])), 0)

    def test_decrypt_rejects_wrong_key(self):
        key = b"k" * KEY_LEN
        wrong_key = b"x" * KEY_LEN
        salt = b"s" * SALT_LEN

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.touch()
            encrypt_data({"site, user, desc": "secret"}, key, salt, str(vault), associated_data="")

            with self.assertRaises(KeyError):
                decrypt_data(wrong_key, str(vault))

    def test_decrypt_rejects_tampered_ciphertext(self):
        key = b"k" * KEY_LEN
        salt = b"s" * SALT_LEN

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.touch()
            encrypt_data({"site, user, desc": "secret"}, key, salt, str(vault), associated_data="")

            record = json.loads(vault.read_text(encoding="utf-8"))
            ciphertext = bytearray.fromhex(record[CIPHERTEXT])
            ciphertext[0] ^= 1
            record[CIPHERTEXT] = ciphertext.hex()
            vault.write_text(json.dumps(record), encoding="utf-8")

            with self.assertRaises(KeyError):
                decrypt_data(key, str(vault))

    def test_encrypt_rejects_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_vault = Path(tmpdir) / "missing.json"

            with self.assertRaises(FileNotFoundError):
                encrypt_data({}, b"k" * KEY_LEN, b"s" * SALT_LEN, str(missing_vault), associated_data="")

    def test_encrypt_rejects_wrong_key_length(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.touch()

            with self.assertRaises(KeyError):
                encrypt_data({}, b"short", b"s" * SALT_LEN, str(vault), associated_data="")

    def test_decrypt_rejects_invalid_vault_record(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.write_text(json.dumps({NONCE: "00" * 12}), encoding="utf-8")

            with self.assertRaises(ValueError):
                decrypt_data(b"k" * KEY_LEN, str(vault))

    def test_get_key_from_pwd_uses_stored_salt(self):
        password = "master-password"
        salt, expected_key = derrive_key(password, b"s" * SALT_LEN)

        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.write_text(
                json.dumps(
                    {
                        SALT: salt.hex(),
                        NONCE: "00" * 12,
                        CIPHERTEXT: "00",
                        ASSOCIATED_DATA: "",
                    }
                ),
                encoding="utf-8",
            )

            returned_salt, returned_key = get_key_from_pwd(password, str(vault))

        self.assertEqual(returned_salt, salt)
        self.assertEqual(returned_key, expected_key)

    def test_get_key_from_pwd_rejects_record_without_salt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir) / "vault.json"
            vault.write_text(
                json.dumps(
                    {
                        NONCE: "00" * 12,
                        CIPHERTEXT: "00",
                        ASSOCIATED_DATA: "",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                get_key_from_pwd("master-password", str(vault))


if __name__ == "__main__":
    unittest.main()
