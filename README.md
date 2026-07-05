# Simple Password Manager

A small command-line password manager written in Python.

This project is mainly a learning project for working with password storage, encryption, key derivation, and basic terminal interfaces. It stores entries in a local encrypted vault file protected by a master password.

## Features

* Create and open an encrypted local vault
* Add entries with website, username, password, and description
* Retrieve saved passwords
* Modify existing entries
* Delete entries
* Generate random passwords
* Copy passwords to the clipboard when possible
* Change the master password
* Save the vault back to disk before exiting

## Security design

The vault is encrypted locally. The master password is used to derive an encryption key with Argon2id. The vault data is encrypted using AES-GCM.

The encrypted vault file stores:

* salt
* nonce
* ciphertext
* associated data field

Writes are done through a temporary file and then replaced atomically, so the old vault should not be overwritten unless the new write succeeds.

## Important warning

This project is not audited and should not be used as a production password manager.

It is a personal learning project. Passwords may still exist in memory while the vault is open, and copied passwords may remain in the system clipboard. Use it carefully and do not rely on it for critical accounts.

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

## Usage

Create a new vault:

```bash
python main.py my.vault --create
```

Open an existing vault:

```bash
python main.py my.vault
```

Inside the program, use the displayed keyboard commands to add, retrieve, modify, or delete entries.

## Notes

* The master password cannot be recovered if forgotten.
* Keep backups of your vault file.
* Do not store the vault file together with your master password.
* Clipboard support depends on the platform. On Termux, clipboard support expects `termux-clipboard-set` to be available.

## Current limitations

* No graphical interface
* No browser integration
* No automatic clipboard clearing
* No formal security audit
* No packaged installer

## Planned improvements

* Add automated tests
* Improve command-line argument handling
* Add safer clipboard handling
* Add optional vault locking
* Improve error messages
* Package the project for easier installation
