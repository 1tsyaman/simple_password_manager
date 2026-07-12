# Testing

The project uses Python's built-in `unittest` framework. The current suite contains 113 tests covering encryption, vault persistence, TOTP support, storage helpers, and migration from vaults created by the `main` branch.

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
python -m unittest tests.test_pwd_manager.PwdManagerPersistenceTests -v
python -m unittest tests.test_pwd_manager.PwdManagerPersistenceTests.test_totp_uri_reconstructs_config_and_secret_after_reload -v
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
├── test_encrypt.py
├── test_entry.py
├── test_keys.py
├── test_pwd_manager.py
├── test_storage_io.py
├── test_totp.py
└── test_vault_migration.py
```

`tests/helpers.py` contains shared master passwords, valid TOTP secrets and URIs, and helpers for creating encrypted fixtures in both the legacy and current vault formats.

## Coverage

### Key derivation

`test_keys.py` verifies:

- Argon2id salt and key lengths
- Reusing a stored salt
- Deterministic derivation with the same password and salt
- Different keys for different passwords or salts

### Encryption

`test_encrypt.py` verifies:

- AES-GCM encryption and decryption round trips
- Rejection of invalid key lengths
- Failure with the wrong key
- Detection of modified ciphertext
- Validation of required encrypted-record fields
- Generation of a new nonce for every write
- Atomic replacement of vault files
- Removal of temporary files after successful writes
- Missing-file handling

### Entry model

`test_entry.py` verifies:

- Entry creation, getters, setters, and display formatting
- Entry identity based on website and username
- Case- and whitespace-insensitive comparisons
- Description and TOTP configuration not affecting entry identity
- JSON serialization and deserialization
- Rejection of missing or incorrectly typed JSON fields
- Assignment and removal of a TOTP configuration

### Password manager

`test_pwd_manager.py` verifies:

- Adding, retrieving, updating, listing, and deleting entries
- Duplicate-entry prevention
- Case- and whitespace-insensitive lookup
- Missing-entry behavior
- Entry lookup by index
- Password generation and password requirement checks
- Adding and replacing TOTP configuration
- Invalid TOTP URIs leaving the previous state unchanged
- Creation of configured `pyotp.TOTP` objects
- Recognition and rejection of supported vault formats
- Empty-vault handling
- Saving and reopening password-only entries
- Saving and reopening mixed password and TOTP entries
- Reconstruction of the TOTP secret and configuration from the stored URI
- Master-password changes and vault re-encryption
- Rejection of an incorrect master password

### TOTP

`test_totp.py` verifies:

- TOTP configuration defaults
- Serialization of URI-compatible configuration values
- Base32 secret validation
- Padded, unpadded, and lowercase secrets
- Minimum decoded secret length
- Rejection of malformed, empty, or non-string secrets
- Parsing of `otpauth://totp` URIs
- URL-decoded issuer and account labels
- Default algorithm, digit count, and period
- Rejection of malformed labels and query parameters
- Rejection of unsupported algorithms, digit counts, and periods
- Issuer consistency between the label and query string

### Storage helpers

`test_storage_io.py` verifies:

- Creating and loading vault files
- Loading previously saved entries
- Missing vault paths
- Invalid parent paths
- Deleting vault files
- Deleting nonexistent vaults
- Rejecting directory paths where a vault file is expected

### Migration from `main`

`test_vault_migration.py` creates encrypted fixtures using the legacy plaintext structure:

```python
{
    "website, username, description": "password"
}
```

It verifies:

- Loading all legacy entries and passwords
- Preserving descriptions, including descriptions containing commas
- Loading and converting empty legacy vaults
- Saving legacy vaults in the new format
- Reopening and saving converted vaults again
- Not inventing TOTP data during migration
- Rejecting malformed or mixed-format vault data

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

## Test isolation

Persistence and migration tests use temporary directories and encrypted fixture files. They do not modify real user vaults or require network access.
