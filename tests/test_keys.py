import unittest
from unittest.mock import patch

from argon2.exceptions import HashingError

from core.errors import KeyDerivationError
from core.keys import (
    ARGON2_MEMORY_COST,
    ARGON2_PARALLELISM,
    ARGON2_TIME_COST,
    KEY_LEN,
    SALT_LEN,
    derive_key,
)


class KeyTests(unittest.TestCase):
    def test_derive_key_uses_supplied_salt_and_argon2id_parameters(self):
        salt = b"s" * SALT_LEN
        key = b"k" * KEY_LEN

        with patch("core.keys.hash_secret_raw", return_value=key) as hash_secret_raw:
            returned_salt, returned_key = derive_key("Master1!", salt)

        self.assertEqual(returned_salt, salt)
        self.assertEqual(returned_key, key)

        kwargs = hash_secret_raw.call_args.kwargs
        self.assertEqual(kwargs["secret"], b"Master1!")
        self.assertEqual(kwargs["salt"], salt)
        self.assertEqual(kwargs["time_cost"], ARGON2_TIME_COST)
        self.assertEqual(kwargs["memory_cost"], ARGON2_MEMORY_COST)
        self.assertEqual(kwargs["parallelism"], ARGON2_PARALLELISM)
        self.assertEqual(kwargs["hash_len"], KEY_LEN)

    def test_derive_key_generates_salt_when_not_supplied(self):
        salt = b"r" * SALT_LEN
        key = b"k" * KEY_LEN

        with patch("core.keys.os.urandom", return_value=salt) as urandom:
            with patch("core.keys.hash_secret_raw", return_value=key):
                returned_salt, returned_key = derive_key("Master1!")

        urandom.assert_called_once_with(SALT_LEN)
        self.assertEqual(returned_salt, salt)
        self.assertEqual(returned_key, key)

    def test_derive_key_wraps_hashing_error(self):
        with patch(
            "core.keys.hash_secret_raw",
            side_effect=HashingError("argon2 failed"),
        ):
            with self.assertRaises(KeyDerivationError):
                derive_key("Master1!", b"s" * SALT_LEN)

    def test_derive_key_wraps_unicode_encode_error(self):
        with self.assertRaises(KeyDerivationError):
            derive_key("\ud800", b"s" * SALT_LEN)


if __name__ == "__main__":
    unittest.main()
