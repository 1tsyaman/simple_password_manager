from pathlib import Path

from core.encrypt import encrypt_data
from core.keys import derive_key


VALID_MASTER_PASSWORD = "Master1!"
VALID_SECRET = "JBSWY3DPEHPK3PXP"
VALID_URI = (
    "otpauth://totp/Example:alice?"
    "secret=JBSWY3DPEHPK3PXP&issuer=Example&algorithm=SHA1&digits=6&period=30"
)


def write_main_branch_vault(
    path: str | Path,
    data: dict[str, str] | None = None,
    password: str = VALID_MASTER_PASSWORD,
) -> Path:
    """Write a vault using the pre-TOTP/main-branch plaintext format."""
    path = Path(path)
    path.touch()

    if data is None:
        data = {
            "github.com, yaman, personal": "github-password",
            "example.com, alice, work": "example-password",
        }

    salt, key = derive_key(password)
    encrypt_data(
        data=data,
        key=key,
        salt=salt,
        file_path=str(path),
        associated_data="",
    )

    return path
