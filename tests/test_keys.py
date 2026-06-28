import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from keys import KEY_LEN, SALT_LEN, derrive_key


class KeyDerivationTests(unittest.TestCase):
    def test_derrive_key_generates_expected_lengths(self):
        salt, key = derrive_key("master-password")

        self.assertEqual(len(salt), SALT_LEN)
        self.assertEqual(len(key), KEY_LEN)

    def test_derrive_key_is_deterministic_with_same_salt(self):
        salt = b"s" * SALT_LEN

        salt_a, key_a = derrive_key("master-password", salt)
        salt_b, key_b = derrive_key("master-password", salt)

        self.assertEqual(salt_a, salt)
        self.assertEqual(salt_b, salt)
        self.assertEqual(key_a, key_b)

    def test_derrive_key_differs_for_different_passwords_with_same_salt(self):
        salt = b"s" * SALT_LEN

        _, key_a = derrive_key("master-password", salt)
        _, key_b = derrive_key("different-password", salt)

        self.assertNotEqual(key_a, key_b)


if __name__ == "__main__":
    unittest.main()
