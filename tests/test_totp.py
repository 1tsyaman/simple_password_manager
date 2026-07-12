import base64
import unittest

from core.totp import TOTP_Config, totp_secret_is_valid
from tests.helpers import VALID_SECRET, VALID_URI


class TOTPSecretValidationTests(unittest.TestCase):
    def test_accepts_16_decoded_bytes(self):
        secret = base64.b32encode(b"a" * 16).decode().rstrip("=")
        self.assertTrue(totp_secret_is_valid(secret))

    def test_accepts_lowercase_and_missing_padding(self):
        self.assertTrue(totp_secret_is_valid(VALID_SECRET.lower()))

    def test_accepts_padded_secret(self):
        secret = base64.b32encode(b"a" * 16).decode()
        self.assertTrue(totp_secret_is_valid(secret))

    def test_rejects_secret_shorter_than_16_decoded_bytes(self):
        secret = base64.b32encode(b"a" * 15).decode().rstrip("=")
        self.assertFalse(totp_secret_is_valid(secret))

    def test_rejects_invalid_base32(self):
        self.assertFalse(totp_secret_is_valid("NOT*BASE32"))

    def test_rejects_empty_secret(self):
        self.assertFalse(totp_secret_is_valid(""))

    def test_rejects_non_string(self):
        self.assertFalse(totp_secret_is_valid(None))  # type: ignore[arg-type]


class TOTPURIParsingTests(unittest.TestCase):
    def test_parses_complete_uri(self):
        result = TOTP_Config.from_uri(VALID_URI)
        self.assertIsNotNone(result)
        config, secret = result  # type: ignore[misc]
        self.assertEqual(secret, VALID_SECRET)
        self.assertEqual(config.issuer, "ACME Co")
        self.assertEqual(config.account, "john.doe@email.com")
        self.assertEqual(config.algorithm, "SHA1")
        self.assertEqual(config.digits, 6)
        self.assertEqual(config.period, 30)

    def test_parses_uri_with_implicit_defaults(self):
        result = TOTP_Config.from_uri(f"otpauth://totp/ACME:user?secret={VALID_SECRET}")
        self.assertIsNotNone(result)
        config, _ = result  # type: ignore[misc]
        self.assertEqual(config.algorithm, "SHA1")
        self.assertEqual(config.digits, 6)
        self.assertEqual(config.period, 30)

    def test_decodes_escaped_label(self):
        result = TOTP_Config.from_uri(
            f"otpauth://totp/My%20Issuer:user%2Btag%40example.com?secret={VALID_SECRET}"
        )
        self.assertIsNotNone(result)
        config, _ = result  # type: ignore[misc]
        self.assertEqual(config.issuer, "My Issuer")
        self.assertEqual(config.account, "user+tag@example.com")

    def test_rejects_wrong_scheme(self):
        self.assertIsNone(TOTP_Config.from_uri(VALID_URI.replace("otpauth", "https", 1)))

    def test_rejects_non_totp_type(self):
        self.assertIsNone(TOTP_Config.from_uri(VALID_URI.replace("totp", "hotp", 1)))

    def test_rejects_label_without_issuer_separator(self):
        self.assertIsNone(TOTP_Config.from_uri(f"otpauth://totp/account?secret={VALID_SECRET}"))

    def test_rejects_empty_issuer(self):
        self.assertIsNone(TOTP_Config.from_uri(f"otpauth://totp/:account?secret={VALID_SECRET}"))

    def test_rejects_empty_account(self):
        self.assertIsNone(TOTP_Config.from_uri(f"otpauth://totp/issuer:?secret={VALID_SECRET}"))

    def test_rejects_missing_secret(self):
        self.assertIsNone(TOTP_Config.from_uri("otpauth://totp/issuer:account"))

    def test_rejects_duplicate_secret(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&secret={VALID_SECRET}"
        self.assertIsNone(TOTP_Config.from_uri(uri))

    def test_rejects_issuer_mismatch(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&issuer=other"
        self.assertIsNone(TOTP_Config.from_uri(uri))

    def test_rejects_unsupported_algorithm(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&algorithm=SHA256"
        self.assertIsNone(TOTP_Config.from_uri(uri))

    def test_rejects_unsupported_digits(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&digits=8"
        self.assertIsNone(TOTP_Config.from_uri(uri))

    def test_rejects_non_integer_digits(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&digits=six"
        self.assertIsNone(TOTP_Config.from_uri(uri))

    def test_rejects_unsupported_period(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&period=60"
        self.assertIsNone(TOTP_Config.from_uri(uri))

    def test_rejects_non_integer_period(self):
        uri = f"otpauth://totp/issuer:account?secret={VALID_SECRET}&period=thirty"
        self.assertIsNone(TOTP_Config.from_uri(uri))


class TOTPConfigTests(unittest.TestCase):
    def test_defaults(self):
        config = TOTP_Config("issuer", "account")
        self.assertEqual(config.algorithm, "SHA1")
        self.assertEqual(config.digits, 6)
        self.assertEqual(config.period, 30)

    def test_to_json_uses_string_values_for_uri_compatible_fields(self):
        config = TOTP_Config("issuer", "account", "SHA1", 6, 30)
        self.assertEqual(
            config.to_json(),
            {
                "issuer": "issuer",
                "account": "account",
                "algorithm": "SHA1",
                "digits": "6",
                "period": "30",
            },
        )
