# App Shell and Navigation

Source: `gui/main.py`, `gui/screens/screen_manager.py`

## Root layout

```text
<SimplePasswordManagerApp>:
    app_screen: MDScreen
        md_bg_color: theme.backgroundColor

        phone_screen: MDScreen
            size_hint_max_x: 500dp
            pos_hint: {center_x: 0.5}
            md_bg_color: theme.secondaryContainerColor

            main_container: MDBoxLayout
                orientation: vertical

                if platform == "android":
                    MDBoxLayout
                        height: 30dp
                        size_hint_y: None

                top_container: MDBoxLayout
                    height: 60dp
                    size_hint_y: None
                    # Replaced by TopBar / SearchBar / SettingsScreenTopBar

                AppScreenManager
                    transition: MDSharedAxisTransition(axis="x")
                    WelcomeScreen
                    VaultScreen
                    SettingsScreen
```

The desktop app therefore still renders a phone-sized interface: `phone_screen` is capped at `500dp` and centered inside the outer screen.

## AppScreenManager composition

```text
<AppScreenManager>:
    vault_lock: Lock
        # Shared protection for the in-memory PwdManager and Settings objects

    WelcomeScreen:
        name: "welcome"

    VaultScreen:
        name: "vault"
        app: running app
        vault_lock: AppScreenManager.vault_lock

    SettingsScreen:
        name: "settings"
        app: running app
        vault_lock: AppScreenManager.vault_lock
```

## Top-bar slot

Every screen owns its logical top bar, but the widget is mounted in the shell's shared `top_container`.

```text
AppScreenManager.switch_top_bar(widget):
    if old child is SearchBar:
        old_search_bar.detach()

    top_container.clear_widgets()
    top_container.add_widget(widget)
```

Current mappings:

```text
WelcomeScreen  → TopBar("Simple Password Manager")
VaultScreen    → SearchBar(...)
SettingsScreen → SettingsScreenTopBar("Settings")
```

## Navigation behavior

```text
WelcomeScreen.on_back()
    → app.stop()

VaultScreen.on_back()
    → switch_screen("welcome")
    → current vault is synchronized before leaving

SettingsScreen back button
    → back_to_vault(...)

Esc / Android back
    → current_screen.on_back()
```

When leaving the vault screen, `AppScreenManager` first asks `VaultScreen.sync_vault(on_exit=True)` unless forced exit has been enabled after a synchronization failure.

## Locking behavior that affects the GUI

```text
SimplePasswordManagerApp
├── inactivity watchdog expires
│   └── close dialogs → AppScreenManager.lock_vault() → WelcomeScreen
├── Android/app pause with lock_on_minimize=True
│   └── lock vault
└── file/QR picker flow
    ├── disable_lockdown()
    └── enable_lockdown() after returning
```

The app dismisses every open `MDDialog` before an automatic lock.
