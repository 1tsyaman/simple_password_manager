# Simple Password Manager

A small command-line password manager written in Python.

This project is mainly a learning project for working with password storage, encryption, key derivation, file handling, and basic terminal interfaces. It stores entries in a local encrypted vault file protected by a master password.

## Features

- Create and open encrypted local vault files
- Add entries with website, username, password, and description
- List saved entries by website and username
- Search entries by website, username, or description
- Retrieve saved passwords
- Copy passwords to the clipboard
- Modify existing entries
- Delete entries
- Generate random passwords
- Change the master password
- Save changes manually
- Save modified vaults on normal exit

## Project structure

```text
simple_password_manager/
├── main.py              # Program entry point and main loop
├── cli/
│   ├── actions.py       # User-facing actions
│   ├── display.py       # Terminal display helpers
│   ├── input.py         # Keyboard and clipboard input helpers
│   └── util.py          # CLI utility functions
├── core/
│   ├── encrypt.py       # Encryption/decryption logic
│   ├── entry.py         # Entry class
│   ├── keys.py          # Key derivation logic
│   └── pwd_manager.py   # Password manager logic
└── storage/
    └── io.py            # Vault loading/creation/deletion helpers
```

## Security design

The vault is encrypted locally.

The master password is used to derive a 256-bit encryption key with Argon2id. Vault data is encrypted using AES-GCM.

The encrypted vault file stores:

- salt
- nonce
- ciphertext
- associated data field

Vault writes are done through a temporary file and then replaced atomically. This helps avoid corrupting the old vault if a write fails.

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

- `[a]` add an entry
- `[g]` generate a random password
- `[m]` modify the master password
- `[f]` search entries
- `[s]` save current changes
- `[q]` quit

When selecting a specific entry, you can modify it, delete it, or retrieve its password.

## Notes

- The master password cannot be recovered if forgotten.
- Keep backups of your vault file.
- Do not store the vault file together with your master password.
- Clipboard support depends on the platform.
- Unsaved changes are saved automatically on normal quit, but manual saving is also available.

## Current limitations

- No graphical interface
- No browser integration
- No automatic clipboard clearing
- No automatic vault locking/watchdog timer
- No formal security audit
- No packaged installer

## Planned improvements

- Improve command-line argument handling
- Add safer clipboard handling
- Add optional vault locking
- Improve error messages
- Package the project for easier installation