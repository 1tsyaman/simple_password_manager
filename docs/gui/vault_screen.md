# Vault Screen

Source: `gui/screens/vault_screen.py` and `gui/widgets/vault_screen/*`

## Screen root

```text
<VaultScreen>:
    name: "vault"
    md_bg_color: theme.secondaryContainerColor

    ├── main_container: MDBoxLayout
    │   # Account content is inserted here dynamically.
    │
    └── PlusButton: MDFabButton
        icon: "plus"
        pos_hint: {right: 0.95, y: 0.05}
        action: open NewAccountDialog
```

## Top bar

The vault replaces the shared top-bar slot with a `SearchBar`.

```text
<SearchBar>:
    supporting_text: "Search accounts..."

    # Normal bar
    ├── leading icon: arrow-left
    │   action: back to WelcomeScreen
    │
    └── trailing icon: dots-vertical
        action: open VaultContextMenu

    # Expanded search view
    ├── leading icon: arrow-left
    │   action: close search view
    ├── MDRecycleView
    │   └── matching AccountEntry rows
    └── trailing icon: window-close
        action: clear query
```

The search runs on every `text` change. The query is split into lowercase keywords; every keyword must occur in at least one value of an account entry.

## Main content — empty state

```text
main_container
└── NoAccountsLabel: MDLabel
    text: "Accounts will appear here."
    halign: center
    valign: middle
```

## Main content — account state

```text
main_container
└── AccountList: MDRecycleView
    do_scroll_x: False

    └── MDRecycleBoxLayout
        orientation: vertical
        row height: 72dp
        spacing: 8dp
        padding: 4dp

        └── AccountEntry: MDListItem  [repeated]
            ├── MDListItemLeadingIcon
            │   icon: "account"
            ├── MDListItemHeadlineText
            │   text: website
            └── MDListItemSupportingText
                text: username

            on_release: open AccountDetailsDialog
```

Accounts are inserted into the recycle view in batches (`BATCH_SIZE = 100`) so a large vault does not block the initial screen transition.

## Add-account flow

```text
PlusButton
└── NewAccountDialog
    ├── Website
    ├── Username
    ├── Password
    │   └── trailing auto-fix icon → generate random password
    ├── Description
    └── Add
        ├── PwdManager.add_entry(...)
        ├── append AccountEntry to AccountList
        └── asynchronous vault sync
```

## Account-details flow

```text
AccountEntry
└── AccountDetailsDialog
    ├── Website        [readonly + copy]
    ├── Username       [readonly + copy]
    ├── Password       [masked + reveal + copy]
    ├── Description    [readonly + copy]
    ├── TOTP           [copy or QR setup action]
    └── buttons
        ├── Dismiss / Cancel
        ├── Modify / Save
        └── Delete
```

See [`DIALOGS.md`](DIALOGS.md) for the view/edit state transition.

## TOTP setup flow

```text
AccountDetailsDialog.TOTP action
└── YesNoDialog("Setup TOTP")
    ├── Android: "Scan"
    │   └── camera QR reader
    └── Desktop: "Select"
        └── ImportFilePicker(type="picture")
            └── decode QR image

valid URI
└── AccountDetailsDialog.set_totp_preview_uri(...)
    └── preview code appears before Save
```

The TOTP display is refreshed once per second while the details dialog is open. Display format:

```text
123 456   •   09s
```

## Vault context menu

Opened from the `dots-vertical` icon.

```text
VaultContextMenu: MDDropdownMenu
├── Settings
│   └── SettingsScreen
├── Rename
│   └── RenameVaultDialog
├── Change Password
│   └── ChangePasswordDialog
├── Export
│   └── ExportFilePicker
└── Delete
    └── YesNoDialog("Delete <vault>?")
```

The menu grows left/down from its caller.

## Export behavior

```text
Export
└── ExportFilePicker
    ├── acquire sync_lock
    ├── final vault sync
    ├── keep lock until export completes
    └── export destination
        ├── Desktop: MDFileManager directory picker
        └── Android: ACTION_OPEN_DOCUMENT_TREE
```

The final sync prevents exporting a stale on-disk vault.
