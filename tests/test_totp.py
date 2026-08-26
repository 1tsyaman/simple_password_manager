import unittest
from unittest.mock import patch

from core.errors import TotpUriError
from core.totp import TOTP_Config, totp_secret_is_valid
from tests.helpers import VALID_SECRET, VALID_URI


class TotpTests(unittest.TestCase):
    def test_from_uri_parses_valid_uri(self):
        config, secret = TOTP_Config.from_uri(VALID_URI)

        self.assertEqual(secret, VALID_SECRET)
        self.assertEqual(config.issuer, "Example")
        self.assertEqual(config.account, "alice")
        self.assertEqual(config.algorithm, "SHA1")
        self.assertEqual(config.digits, 6)
        self.assertEqual(config.period, 30)

    def test_from_uri_accepts_issuer_from_label_only(self):
        config, secret = TOTP_Config.from_uri(
            f"otpauth://totp/Example:alice?secret={VALID_SECRET}"
        )

        self.assertEqual(secret, VALID_SECRET)
        self.assertEqual(config.issuer, "Example")
        self.assertEqual(config.account, "alice")

    def test_from_uri_accepts_issuer_from_query_only(self):
        config, secret = TOTP_Config.from_uri(
            f"otpauth://totp/alice?secret={VALID_SECRET}&issuer=Example"
        )

        self.assertEqual(secret, VALID_SECRET)
        self.assertEqual(config.issuer, "Example")
        self.assertEqual(config.account, "alice")

    def test_from_uri_decodes_label(self):
        config, _ = TOTP_Config.from_uri(
            f"otpauth://totp/Example%20Inc:alice%40example.com?"
            f"secret={VALID_SECRET}&issuer=Example%20Inc"
        )

        self.assertEqual(config.issuer, "Example Inc")
        self.assertEqual(config.account, "alice@example.com")

    def test_from_uri_rejects_invalid_scheme_or_type(self):
        invalid = [
            f"https://totp/Example:alice?secret={VALID_SECRET}&issuer=Example",
            f"otpauth://hotp/Example:alice?secret={VALID_SECRET}&issuer=Example",
        ]

        for uri in invalid:
            with self.subTest(uri=uri):
                with self.assertRaises(TotpUriError):
                    TOTP_Config.from_uri(uri)

    def test_from_uri_rejects_missing_or_invalid_label(self):
        invalid = [
            f"otpauth://totp/?secret={VALID_SECRET}&issuer=Example",
            f"otpauth://totp/:alice?secret={VALID_SECRET}&issuer=Example",
            f"otpauth://totp/Example:?secret={VALID_SECRET}&issuer=Example",
        ]

        for uri in invalid:
            with self.subTest(uri=uri):
                with self.assertRaises(TotpUriError):
                    TOTP_Config.from_uri(uri)

    def test_from_uri_rejects_missing_or_invalid_secret(self):
        invalid = [
            "otpauth://totp/Example:alice?issuer=Example",
            "otpauth://totp/Example:alice?secret=ABC&issuer=Example",
        ]

        for uri in invalid:
            with self.subTest(uri=uri):
                with self.assertRaises(TotpUriError):
                    TOTP_Config.from_uri(uri)

    def test_from_uri_rejects_missing_issuer(self):
        with self.assertRaises(TotpUriError):
            TOTP_Config.from_uri(
                f"otpauth://totp/alice?secret={VALID_SECRET}"
            )

    def test_from_uri_rejects_mismatching_issuers(self):
        with self.assertRaises(TotpUriError):
            TOTP_Config.from_uri(
                f"otpauth://totp/LabelIssuer:alice?"
                f"secret={VALID_SECRET}&issuer=QueryIssuer"
            )

    def test_from_uri_rejects_unsupported_algorithm(self):
        with self.assertRaises(TotpUriError):
            TOTP_Config.from_uri(
                f"otpauth://totp/Example:alice?"
                f"secret={VALID_SECRET}&issuer=Example&algorithm=SHA256"
            )

    def test_from_uri_rejects_unsupported_digits(self):
        with self.assertRaises(TotpUriError):
            TOTP_Config.from_uri(
                f"otpauth://totp/Example:alice?"
                f"secret={VALID_SECRET}&issuer=Example&digits=8"
            )

    def test_from_uri_rejects_unsupported_period(self):
        with self.assertRaises(TotpUriError):
            TOTP_Config.from_uri(
                f"otpauth://totp/Example:alice?"
                f"secret={VALID_SECRET}&issuer=Example&period=60"
            )

    def test_from_uri_rejects_non_numeric_digits_or_period(self):
        invalid = [
            (
                f"otpauth://totp/Example:alice?"
                f"secret={VALID_SECRET}&issuer=Example&digits=six"
            ),
            (
                f"otpauth://totp/Example:alice?"
                f"secret={VALID_SECRET}&issuer=Example&period=thirty"
            ),
        ]

        for uri in invalid:
            with self.subTest(uri=uri):
                with self.assertRaises(TotpUriError):
                    TOTP_Config.from_uri(uri)

    def test_totp_secret_validation(self):
        self.assertTrue(totp_secret_is_valid(VALID_SECRET))
        self.assertTrue(totp_secret_is_valid(VALID_SECRET.lower()))
        self.assertFalse(totp_secret_is_valid("ABC"))
        self.assertFalse(totp_secret_is_valid("not base32!"))

    def test_seconds_remaining_uses_configured_period(self):
        config = TOTP_Config(period=30)

        with patch("core.totp.time", return_value=61.0):
            self.assertEqual(config.seconds_remaining(), 29)

    def test_to_json_uses_serializable_values(self):
        config = TOTP_Config(
            issuer="Example",
            account="alice",
            algorithm="SHA1",
            digits=6,
            period=30,
        )

        self.assertEqual(
            config.to_json(),
            {
                "issuer": "Example",
                "account": "alice",
                "algorithm": "SHA1",
                "digits": "6",
                "period": "30",
            },
        )


if __name__ == "__main__":
    unittest.main()
