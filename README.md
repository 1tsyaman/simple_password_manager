# Simple Password Manager

A small command-line password manager written in Python.

This project is primarily a learning project for working with password storage, authenticated encryption, key derivation, file handling, TOTP-based two-factor authentication, and terminal interfaces. It stores passwords and optional TOTP configuration in a local encrypted vault protected by a master password.

## Features

* Create and open encrypted local vault files
* Add entries with a website, username, password, and description
* List saved entries by website and username
* Search entries interactively by website, username, or description
* Retrieve and copy saved passwords
* Modify and delete existing entries
* Generate random passwords
* Store TOTP configuration using standard `otpauth://totp` URIs
* Generate TOTP codes and display their remaining validity time
* Copy generated TOTP codes to the clipboard
* Change the master password
* Save changes manually
* Save modified vaults automatically on normal exit
* Load pre-TOTP vaults and convert them to the current format when saved
* Automatically exit after 60 seconds of inactivity
* Reset the inactivity timer whenever user input is received

## Project structure

```text
simple_password_manager/
├── main.py              # Program entry point and main menu
├── cli/
│   ├── actions.py       # User-facing password and TOTP actions
│   ├── display.py       # Terminal display helpers
│   ├── input.py         # Keyboard and clipboard input helpers
│   ├── util.py          # CLI utility functions
│   └── watchdog.py      # Inactivity watchdog
├── core/
│   ├── encrypt.py       # AES-GCM encryption and decryption
│   ├── entry.py         # Entry model
│   ├── keys.py          # Argon2id key derivation
│   ├── pwd_manager.py   # Vault, password, TOTP, and migration logic
│   └── totp.py          # TOTP URI parsing and validation
└── storage/
    └── io.py            # Vault loading, creation, and deletion
```

## Security design

The vault is encrypted locally.

The master password is used to derive a 256-bit encryption key with Argon2id. Vault data is encrypted and authenticated using AES-GCM.

The encrypted vault file stores:

* Salt
* Nonce
* Ciphertext
* Associated data field

Passwords and TOTP URIs are contained inside the encrypted vault data. A TOTP URI includes the account's TOTP secret, so it must be protected with the same care as a password.

Vault writes use a temporary file followed by atomic replacement. This reduces the risk of corrupting the previous vault if a write fails.

Each encryption operation generates a new nonce.

## Vault formats and migration

The current decrypted vault structure stores a password and a TOTP URI for each entry:

```python
{
    "website, username, description": {
        "pwd": "password",
        "totp_uri": "otpauth://totp/..."
    }
}
```

For entries without TOTP enabled, `totp_uri` is an empty string.

Vaults created before TOTP support used this structure:

```python
{
    "website, username, description": "password"
}
```

The program can load this pre-TOTP format. Saving the loaded vault converts it to the current format.

Back up important vault files before converting them with a newer version of the program.

## Important warning

This project is not audited and should not be used as a production password manager.

It is a personal learning project. Passwords and TOTP secrets may exist in process memory while the vault is open. Copied values may also remain in the system clipboard or clipboard history.

Do not rely on this project for critical accounts or as the only copy of important credentials.

## Installation

Clone the repository:

```bash
git clone https://github.com/1tsyaman/simple_password_manager.git
cd simple_password_manager
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### Clipboard support on Linux

Clipboard support uses `pyperclip`.

On Linux, install `xclip` so copying passwords and TOTP codes works:

```bash
sudo apt install xclip
```

On Termux, clipboard support expects `termux-clipboard-set` to be available.

## Usage

Create a new vault:

```bash
python main.py my.vault --create
```

Open an existing vault:

```bash
python main.py my.vault
```

Creating a vault at an existing path requires two confirmations before the old vault is deleted and replaced.

### Main menu

The main menu displays the available commands and a paginated list of entries.

* `[a]` — add an entry
* `[g]` — generate a random password
* `[m]` — change the master password
* `[f]` — search entries
* `[s]` — save current changes
* `[q]` — quit
* `[p]` / `[n]` — move between pages when available
* A displayed number — select the corresponding entry

### Entry menu

After selecting an entry:

* `[m]` — modify the entry
* `[d]` — delete the entry
* `[r]` — retrieve its password
* `[g]` — generate its TOTP code, when TOTP is configured
* `[backspace]` — return to the previous menu

The modification menu can update the website, username, password, description, or TOTP configuration.

### TOTP setup

To enable TOTP for an entry:

1. Select the entry.
2. Choose the modify option.
3. Choose the TOTP/two-factor-authentication option.
4. Paste the complete `otpauth://totp/...` URI.

The program validates the URI and its Base32 secret before storing it.

TOTP retrieval displays the current code together with the number of seconds for which it remains valid.

### Inactivity watchdog

The program includes a 60-second inactivity watchdog.

The timer resets whenever the user interacts with the application, including while entering passwords and using menu commands.

When the timeout is reached, the process exits immediately without saving unsaved changes. Use `[s]` to save important changes manually.

A normal exit with `[q]` saves the vault automatically when it has been modified.

Pressing `Ctrl+C` offers a chance to save before exiting. Pressing `Ctrl+C` again exits without saving.

## Password generation

Generated passwords are 24 characters long and contain at least:

* One lowercase letter
* One uppercase letter
* One digit
* One special character

Master passwords must meet the minimum password requirements enforced by the application. A forgotten master password cannot be recovered.

## Notes

* The master password cannot be recovered if forgotten.
* Keep backups of the vault file.
* Do not store the vault together with its master password.
* Clipboard support depends on the operating system.
* Unsaved changes are saved automatically on a normal quit.
* Unsaved changes are discarded when the inactivity watchdog triggers.
* The watchdog exits the application rather than locking and reopening the vault.
* TOTP secrets are stored as part of encrypted TOTP URIs.

## Current limitations

* No graphical interface
* No browser integration
* No automatic clipboard clearing
* No automatic vault locking and unlocking
* No formal security audit
* No packaged installer
* TOTP support is currently limited to SHA-1, six-digit codes, and a 30-second period

## Planned improvements

* Improve command-line argument handling
* Add safer clipboard handling
* Add optional vault locking and unlocking
* Support additional TOTP algorithms and configurations
* Improve error messages
* Package the project for easier installation

## AI Usage Disclaimer

The application code in this repository was written by the author. The automated test suite available in the separate testing branch was generated with the assistance of an AI agent and subsequently reviewed and adjusted to match the project's current design and expected behavior.
