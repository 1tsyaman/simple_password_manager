# Dialogs

This file documents every `MDDialog` class directly used by the current screen flows.

## LoginDialog

Source: `gui/dialogs/selection_screen/login_dialog.py`

```text
LoginDialog: MDDialog
├── MDDialogIcon
│   icon: "safe"
├── MDDialogHeadlineText
│   text: "Unlock <vault>"
├── MDDialogContentContainer [vertical]
│   └── InputField
│       title: "Password"
│       leading icon: "lock"
│       password: True
│       trailing icon: eye / eye-off
└── MDDialogButtonContainer
    ├── spacer
    ├── Cancel [text]
    └── Accept [text]
```

`Accept` forwards the password to `AppScreenManager.open_vault()`; validation failures are displayed in the password field's error helper.

---

## NewVaultDialog

Source: `gui/dialogs/selection_screen/new_vault_dialog.py`

```text
NewVaultDialog: MDDialog
├── icon: safe
├── headline: "Create vault"
├── content [vertical, spacing=30dp]
│   ├── InputField("Name")
│   ├── InputField("Password", password=True)
│   └── InputField("Confirm Password", password=True)
└── buttons
    ├── Cancel
    └── Create
```

---

## NewAccountDialog

Source: `gui/dialogs/vault_screen/new_account_dialog.py`

```text
NewAccountDialog: MDDialog
├── icon: account
├── headline: "Add new account"
├── content [vertical, spacing=30dp]
│   ├── InputField("Website", icon="web")
│   ├── InputField("Username", icon="account")
│   ├── InputField("Password", icon="key")
│   │   └── trailing icon: auto-fix → generate password
│   └── InputField("Description", icon="text")
└── buttons
    ├── Cancel
    └── Add
```

---

## AccountDetailsDialog

Source: `gui/dialogs/vault_screen/account_details_dialog.py`

### View mode

```text
AccountDetailsDialog: MDDialog
├── icon: account-details
├── headline: "Account details"
├── content [vertical, spacing=12dp]
│   ├── ReadOnlyTextField
│   │   leading_icon: web
│   │   text: website
│   │   trailing action: copy
│   ├── ReadOnlyTextField
│   │   leading_icon: account
│   │   text: username
│   │   trailing action: copy
│   ├── PasswordReadOnlyText
│   │   leading_icon: key
│   │   masked: True
│   │   inline eye icon: show/hide
│   │   trailing action: copy
│   ├── ReadOnlyTextField
│   │   leading_icon: text
│   │   text: description
│   │   trailing action: copy
│   └── TotpReadOnlyTextField
│       leading_icon: timer-lock
│       text: "123 456   •   09s" OR "TOTP not configured"
│       trailing action: copy TOTP when configured
└── buttons
    ├── Dismiss
    ├── Modify
    └── Delete [error color]
```

### Modify mode

Pressing `Modify` changes the existing dialog rather than opening a second editor.

```text
AccountDetailsDialog [modify mode]
├── website field: editable
├── username field: editable
├── password field: editable + unmasked
├── description field: editable
├── TOTP field
│   └── trailing button switches from copy → qrcode setup
└── buttons
    ├── Cancel   # restore original values
    ├── Save
    └── Delete   # disabled / 50% opacity
```

After a successful save, fields return to read-only mode and the account row is updated in place.

### Delete confirmation

```text
Delete
└── YesNoDialog
    icon: alert-circle
    headline: "Are you sure?"
    message: "Deleted accounts cannot be restored"
```

---

## RenameVaultDialog

Source: `gui/dialogs/vault_screen/rename_vault_dialog.py`

```text
RenameVaultDialog: MDDialog
├── headline: "Rename vault"
├── content
│   └── InputField
│       title: "Vault name"
│       icon: safe
│       text: current vault name
└── buttons
    ├── Cancel
    └── Confirm
```

---

## ChangePasswordDialog

Source: `gui/dialogs/vault_screen/change_password_dialog.py`

```text
ChangePasswordDialog: MDDialog
├── icon: safe
├── headline: "Change vault password"
├── content [vertical, spacing=30dp]
│   ├── InputField("New Password", password=True)
│   └── InputField("Confirm New Password", password=True)
└── buttons
    ├── Cancel
    └── Confirm
```

---

## YesNoDialog

Source: `gui/dialogs/yes_no_dialog.py`

Reusable two-choice confirmation dialog.

```text
YesNoDialog: MDDialog
├── [optional] MDDialogIcon(icon)
├── MDDialogHeadlineText(headline)
├── MDDialogSupportingText(message)
└── MDDialogButtonContainer
    ├── spacer
    ├── Yes / custom yes_text
    ├── No / custom no_text
    └── spacer
```

Either option can be rendered in the theme's error color; `yes` is the default red option.

Current uses include vault deletion, account deletion, and TOTP QR setup.

---

## ErrorDialog

Source: `gui/dialogs/error_dialog.py`

```text
ErrorDialog: MDDialog
├── icon: alert-circle
├── headline: error_title
├── supporting text: error_message
└── buttons
    ├── spacer
    ├── first action (default label: "dismiss")
    └── [optional] second action
```

If no first callback is supplied, the first action simply dismisses the dialog.
