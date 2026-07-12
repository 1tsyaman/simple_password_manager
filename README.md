# Simple Password Manager

A small command-line password manager written in Python.

This project is mainly a learning project for working with password storage, encryption, key derivation, file handling, and basic terminal interfaces. It stores entries in a local encrypted vault file protected by a master password.

## Features

* Create and open encrypted local vault files
* Add entries with website, username, password, and description
* List saved entries by website and username
* Search entries by website, username, or description
* Retrieve saved passwords
* Copy passwords to the clipboard
* Modify existing entries
* Delete entries
* Generate random passwords
* Change the master password
* Save changes manually
* Save modified vaults on normal exit
* Automatically exit after 60 seconds of inactivity
* Reset the inactivity timer whenever user input is received

## Project structure

```text
simple_password_manager/
├── main.py              # Program entry point and main loop
├── cli/
│   ├── actions.py       # User-facing actions
│   ├── display.py       # Terminal display helpers
│   ├── input.py         # Keyboard and clipboard input helpers
│   ├── util.py          # CLI utility functions
│   └── watchdog.py      # Inactivity watchdog
├── core/
│   ├── encrypt.py       # Encryption/decryption logic
│   ├── entry.py         # Entry class
│   ├── keys.py          # Key derivation logic
│   └── pwd_manager.py   # Password manager logic
└── storage/
    └── io.py            # Vault loading, creation, and deletion helpers
```

## Security design

The vault is encrypted locally.

The master password is used to derive a 256-bit encryption key with Argon2id. Vault data is encrypted using AES-GCM.

The encrypted vault file stores:

* Salt
* Nonce
* Ciphertext
* Associated data field

Vault writes are done through a temporary file and then replaced atomically. This helps avoid corrupting the previous vault if a write fails.

## Important warning

This project is not audited and should not be used as a production password manager.

It is a personal learning project. Passwords may still exist in memory while the vault is open, and copied passwords may remain in the system clipboard or clipboard history.

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

Install dependencies:

```bash
pip install -r requirements.txt
```

### Clipboard support on Linux

Clipboard support uses `pyperclip`.

On Linux, install `xclip` so copying passwords works:

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

Inside the program, use the displayed keyboard commands.

Main actions include:

* `[a]` add an entry
* `[g]` generate a random password
* `[m]` modify the master password
* `[f]` search entries
* `[s]` save current changes
* `[q]` quit

When selecting a specific entry, you can modify it, delete it, or retrieve its password.

### Inactivity watchdog

The program includes an inactivity watchdog.

If no user input is received for 60 seconds, the process exits automatically. The timer is reset whenever the user interacts with the program, including while entering passwords or using menu commands.

A watchdog timeout exits immediately and does not save unsaved vault changes. Use `[s]` to save important changes manually.

Normal quitting with `[q]` still saves modified vaults automatically.

## Notes

* The master password cannot be recovered if forgotten.
* Keep backups of your vault file.
* Do not store the vault file together with your master password.
* Clipboard support depends on the platform.
* Unsaved changes are saved automatically on normal quit.
* Unsaved changes are discarded when the inactivity watchdog triggers.
* The watchdog exits the application rather than locking and reopening the active vault.

## Current limitations

* No graphical interface
* No browser integration
* No automatic clipboard clearing
* No formal security audit
* No packaged installer

## Planned improvements

* Improve command-line argument handling
* Add safer clipboard handling
* Add optional vault locking and unlocking
* Improve error messages
* Package the project for easier installation

## AI Usage Disclaimer

The application code in this repository was written by the author. The automated test suite was generated with the assistance of an AI agent and subsequently reviewed and adjusted to match the project's current design and expected behavior.
