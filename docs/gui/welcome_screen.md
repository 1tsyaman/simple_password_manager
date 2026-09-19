# Welcome Screen

Source: `gui/screens/welcome_screen.py`, `gui/widgets/welcome_screen/card_widgets.py`

## Screen root

```text
<WelcomeScreen>:
    name: "welcome"
    md_bg_color: theme.secondaryContainerColor

    main_container: MDAnchorLayout
        anchor_x: center
        anchor_y: center
        # Exactly one of the two cards below is inserted here.
```

On `on_pre_enter`, the screen rebuilds its content and installs:

```text
TopBar
    title: "Simple Password Manager"
```

## State A — no vault exists

```text
main_container
└── NoVaultWidget: DecorativeCard
    width: 320dp
    height: 190dp
    orientation: vertical
    style: elevated
    padding: 24dp
    spacing: 8dp

    ├── MDLabel
    │   text: "Set up your vault"
    │   font_style: Title / medium
    │   halign: center
    │
    ├── Widget
    │   height: 16dp
    │
    ├── MDButton [filled]
    │   text: "Create Vault"
    │   action: open NewVaultDialog
    │
    └── MDButton [text]
        text: "Import Vault"
        action: open ImportFilePicker(type=".vault")
```

## State B — a vault exists

The current design is single-vault-oriented: the first item returned by `get_vault_list()` is used.

```text
main_container
└── OpenVaultWidget: DecorativeCard
    width: 320dp
    height: 150dp
    orientation: vertical
    style: elevated
    padding: 24dp
    spacing: 8dp

    ├── MDLabel
    │   text: "Welcome Back!"
    │   font_style: Title / medium
    │   halign: center
    │
    ├── Widget
    │   height: 10dp
    │
    └── MDButton [filled]
        text: "Open Vault"
        action: open LoginDialog(vault)
```

The theme is read from that vault before login and applied immediately.

On the first welcome-screen load after app startup (or directly after a vault import), the `LoginDialog` is also opened automatically.

## Create-vault flow

```text
Create Vault button
└── NewVaultDialog
    ├── Name
    ├── Password
    ├── Confirm Password
    └── Create
        └── VaultSession(new_vault=True)
            ├── create PwdManager
            ├── create Settings
            └── AppScreenManager.open_new_vault(...)
                └── VaultScreen
```

Validation errors are displayed inside the relevant `InputField` helper/error text.

## Import-vault flow

```text
Import Vault button
└── ImportFilePicker(type=".vault")
    ├── Desktop: MDFileManager selects one .vault file
    └── Android: ACTION_OPEN_DOCUMENT

successful import
└── finish_importing_vault()
    ├── mark imported vault for fresh settings creation
    ├── refresh WelcomeScreen
    └── automatically open LoginDialog
```

## Unlock flow

```text
Open Vault
└── LoginDialog
    └── Accept
        └── AppScreenManager.open_vault(...)
            ├── VaultSession(...)
            ├── load PwdManager
            ├── load Settings
            └── VaultScreen
```
