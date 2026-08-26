# Testing

The project uses Python's built-in `unittest` framework. The current suite contains 146 tests covering the backend, encryption and vault persistence, TOTP support, storage helpers, legacy vault migration, CLI behavior, main dispatch, and save-on-quit handling.

## Running the tests

Run the complete suite from the repository root:

```bash
python -m unittest discover -v
```

Run a single module:

```bash
python -m unittest tests.test_totp -v
```

Run a single test class or test:

```bash
python -m unittest tests.test_pwd_manager.PwdManagerTests -v
python -m unittest tests.test_pwd_manager.PwdManagerTests.test_encrypt_and_from_encrypted_file_round_trip -v
```

The command should finish with:

```text
OK
```

## Test structure

```text
tests/
├── __init__.py
├── helpers.py
├── test_cli_actions.py
├── test_cli_display.py
├── test_cli_input.py
├── test_cli_util.py
├── test_encrypt.py
├── test_entry.py
├── test_keys.py
├── test_main.py
├── test_pwd_manager.py
├── test_save_on_quit.py
├── test_storage_io.py
├── test_totp.py
└── test_vault_migration.py
```

`tests/helpers.py` contains the shared master password, a valid TOTP secret and URI, and a helper for creating encrypted vault fixtures in the legacy `main`-branch format.

## Coverage

### Key derivation

`test_keys.py` verifies:

- Argon2id is called with the configured time, memory, parallelism, and key-length parameters
- Reusing a supplied salt
- Generating a new salt when none is supplied
- Conversion of Argon2 hashing failures into `KeyDerivationError`
- Conversion of password encoding failures into `KeyDerivationError`

### Encryption

`test_encrypt.py` verifies:

- AES-GCM encryption and decryption round trips
- The expected encrypted-record structure
- Rejection of invalid key lengths
- Failure with the wrong key through `CorruptedVaultError`
- Detection of malformed vault JSON and missing encrypted-record fields through `VaultFormatError`
- Missing-file handling
- Reading the stored salt when deriving a key from a password
- Rejection of invalid stored salts

### Entry model

`test_entry.py` verifies:

- Entry creation, getters, setters, and display formatting
- Entry identity based on website and username
- Case- and whitespace-insensitive comparisons
- Description not affecting entry identity
- Assignment and removal of a TOTP configuration
- `EntryHasNoTotp` when no TOTP configuration exists
- JSON serialization and deserialization
- Rejection of missing or incorrectly typed JSON fields through `InvalidEntryJSON`

### Password manager

`test_pwd_manager.py` verifies:

- Adding, retrieving, updating, listing, and deleting entries
- Duplicate-entry prevention through `EntryExistsError`
- Missing-entry handling through `NoSuchEntryError`
- Case- and whitespace-insensitive lookup
- Entry lookup by index
- Password and description retrieval
- TOTP configuration and code generation
- Missing and malformed TOTP handling
- Serialization of the current vault format
- Snapshot independence
- Master-password changes, re-encryption, rollback on save failure, and password requirements
- Creating new managers from a master password
- Saving and reopening encrypted vaults
- Wrong-password/corrupted-vault handling
- Rejection of invalid decrypted vault formats
- Random password generation and password requirement checks

### TOTP

`test_totp.py` verifies:

- Parsing valid `otpauth://totp` URIs
- Issuers supplied through the label or query string
- URL-decoded issuer and account labels
- Base32 secret validation
- Rejection of invalid schemes, OTP types, labels, secrets, and issuers
- Issuer consistency between the label and query string
- Rejection of unsupported algorithms, digit counts, and periods
- Rejection of non-numeric digit and period values
- Remaining-time calculation
- Serialization of TOTP configuration values

### Storage helpers

`test_storage_io.py` verifies:

- Loading existing vaults
- Creating new vaults
- GUI path construction and `.vault` extension handling
- Cleanup when GUI vault creation fails
- Listing vault files
- Vault existence checks
- Missing vault and invalid parent paths
- Deleting vault files
- Rejecting directory paths where a vault file is expected

### Migration from `main`

`test_vault_migration.py` creates encrypted fixtures using the legacy plaintext structure:

```python
{
    "website, username, description": "password"
}
```

It verifies:

- Loading legacy entries and passwords
- Preserving descriptions
- Not inventing TOTP data during migration
- Rejecting malformed legacy entries
- Rejecting non-string legacy passwords

### CLI actions

`test_cli_actions.py` verifies:

- Adding entries with manual or generated passwords
- Confirmation and cancellation behavior
- Duplicate-entry handling
- Removing entries
- Password copying
- Missing-entry and missing-TOTP handling
- Modifying websites, usernames, descriptions, passwords, and the master password
- Saving changes and handling backend save errors
- Interactive search and query filtering
- Double-confirmation for destructive actions
- Random-password generation behavior

### CLI display and input

`test_cli_display.py` and `test_cli_input.py` verify:

- Paginated list formatting
- Terminal color formatting
- Screen clearing and footer output
- Key classification and keystroke handling
- Confirmation/input polling
- Clipboard handling, including the Termux fallback
- Standard input and password input wrappers

### CLI utilities

`test_cli_util.py` verifies:

- Selection-index validation
- Previous/next page prompts
- Ordered list differences
- Entry filtering across website, username, and description
- Avoiding duplicate results when multiple fields match

### Main dispatch

`test_main.py` verifies:

- Starting the GUI when no command-line arguments are supplied
- Forwarding command-line arguments to the CLI

### Save on quit

`test_save_on_quit.py` verifies:

- Saving on `Ctrl+C` when confirmed
- Quitting without saving when declined
- A second `Ctrl+C` aborting the save prompt
- Handling backend save failures
- Timeout-triggered exits without a save prompt

## Current vault format

The current plaintext structure before encryption is:

```python
{
    "website, username, description": {
        "pwd": "password",
        "totp_uri": ""
    }
}
```

For entries with TOTP enabled, `totp_uri` contains the complete `otpauth://` URI. For password-only entries, it is an empty string.

The TOTP secret is not stored as a separate persistent field. It is reconstructed from the URI after the vault is decrypted and loaded.

## Error handling

Backend failure cases are tested using the current exception-based API rather than sentinel strings or `None`. This includes errors such as:

- `EntryExistsError`
- `NoSuchEntryError`
- `EntryHasNoTotp`
- `PasswordError` / `PasswordRequirementsError`
- `TotpUriError`
- `VaultFormatError`
- `CorruptedVaultError`
- `KeyLengthError`
- `KeyDerivationError`

## Test isolation

Persistence and migration tests use temporary directories and encrypted fixture files. They do not modify real user vaults or require network access.
