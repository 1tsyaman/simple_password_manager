from __future__ import annotations

from pathlib import Path

from core.encrypt import encrypt_data
from core.keys import derrive_key

VALID_MASTER_PASSWORD = "StrongMaster1!"
NEW_MASTER_PASSWORD = "NewStrongMaster2@"
VALID_SECRET = "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"
SECOND_VALID_SECRET = "KRSXG5DSNFXGOIDBNZXXEZJAN52XGZLS"

VALID_URI = (
    "otpauth://totp/ACME%20Co:john.doe%40email.com"
    f"?secret={VALID_SECRET}&issuer=ACME%20Co&algorithm=SHA1&digits=6&period=30"
)
SECOND_VALID_URI = (
    "otpauth://totp/Other%20Issuer:other%40email.com"
    f"?secret={SECOND_VALID_SECRET}&issuer=Other%20Issuer&algorithm=SHA1&digits=6&period=30"
)


def write_main_branch_vault(
    path: Path,
    data: dict[str, str],
    password: str = VALID_MASTER_PASSWORD,
) -> None:
    """Write the exact plaintext structure used by main before TOTP support."""
    path.touch()
    salt, key = derrive_key(password)
    encrypt_data(data=data, key=key, salt=salt, file_path=str(path), associated_data="")


def write_new_format_vault(
    path: Path,
    data: dict[str, dict[str, str]],
    password: str = VALID_MASTER_PASSWORD,
) -> None:
    """Write an encrypted vault using the current {pwd, totp_uri} value format."""
    path.touch()
    salt, key = derrive_key(password)
    encrypt_data(data=data, key=key, salt=salt, file_path=str(path), associated_data="")
