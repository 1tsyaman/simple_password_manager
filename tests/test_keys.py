import unittest

from core.keys import KEY_LEN, SALT_LEN, derrive_key


class KeyDerivationTests(unittest.TestCase):
    def test_generates_expected_salt_and_key_lengths(self):
        salt, key = derrive_key("password")
        self.assertEqual(len(salt), SALT_LEN)
        self.assertEqual(len(key), KEY_LEN)

    def test_reuses_provided_salt(self):
        salt = bytes(range(SALT_LEN))
        returned_salt, _ = derrive_key("password", salt)
        self.assertEqual(returned_salt, salt)

    def test_same_password_and_salt_produce_same_key(self):
        salt = bytes(range(SALT_LEN))
        self.assertEqual(derrive_key("password", salt)[1], derrive_key("password", salt)[1])

    def test_different_password_changes_key(self):
        salt = bytes(range(SALT_LEN))
        self.assertNotEqual(derrive_key("password", salt)[1], derrive_key("different", salt)[1])

    def test_different_salt_changes_key(self):
        self.assertNotEqual(derrive_key("password", b"a" * SALT_LEN)[1], derrive_key("password", b"b" * SALT_LEN)[1])
