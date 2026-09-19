# GUI Structure

This documentation describes the Kivy/KivyMD GUI as it exists on `main` at commit:

`357c9230fcaab2fd11c7ec6e4e850fefdb23209c`

Commit title: **Fixed renaming logic and switch sync_lock to RLock**

The diagrams use a **KV-like pseudo-syntax**. They are intended to make the widget hierarchy easy to read; they are not executable `.kv` files.

## Documentation map

- [`gui/APP_SHELL.md`](gui/APP_SHELL.md) — root app layout, top-bar slot, screen manager, navigation
- [`gui/WELCOME_SCREEN.md`](gui/WELCOME_SCREEN.md) — first-run and unlock states
- [`gui/VAULT_SCREEN.md`](gui/VAULT_SCREEN.md) — account list, search, context menu, account/TOTP flows
- [`gui/SETTINGS_SCREEN.md`](gui/SETTINGS_SCREEN.md) — dynamically generated settings UI
- [`gui/DIALOGS.md`](gui/DIALOGS.md) — all GUI dialogs used by the screens
- [`gui/WIDGETS.md`](gui/WIDGETS.md) — reusable custom widgets and file pickers

## High-level hierarchy

```text
SimplePasswordManagerApp
└── app_screen: MDScreen
    └── phone_screen: MDScreen                 # max width 500dp, centered
        └── main_container: MDBoxLayout        # vertical
            ├── [Android only] status spacer   # 30dp
            ├── top_container: MDBoxLayout     # 60dp; content swapped per screen
            └── AppScreenManager
                ├── WelcomeScreen(name="welcome")
                ├── VaultScreen(name="vault")
                └── SettingsScreen(name="settings")
```

The app keeps the top bar outside the `MDScreenManager`. Each screen replaces the contents of `top_container` when it becomes active.

## Main navigation

```text
WelcomeScreen
  ├── create/import vault
  └── LoginDialog
        └── successful unlock
              ↓
          VaultScreen
              ├── back → WelcomeScreen
              └── vault menu → SettingsScreen
                                    └── back → VaultScreen
```

The screen manager uses `MDSharedAxisTransition(transition_axis="x")`.

## Important dynamic UI states

```text
WelcomeScreen.main_container
├── no local vault     → NoVaultWidget
└── vault exists       → OpenVaultWidget

VaultScreen.main_container
├── no accounts        → NoAccountsLabel
└── accounts exist     → AccountList

AccountDetailsDialog
├── view mode          → readonly fields + copy buttons
└── modify mode        → editable fields + TOTP setup action

FilePicker
├── desktop            → KivyMD MDFileManager
└── Android            → native Android document/tree picker
```

## Source entry points

- `gui/main.py`
- `gui/screens/screen_manager.py`
- `gui/screens/welcome_screen.py`
- `gui/screens/vault_screen.py`
- `gui/screens/settings_screen.py`
