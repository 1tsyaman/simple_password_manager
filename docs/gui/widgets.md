# Custom Widgets

This file describes the reusable GUI building blocks used by the current screens and dialogs.

## Text-field family

### FocusableTextField

Source: `gui/widgets/focusable_text_field.py`

```text
FocusableTextField: MDTextField + AndroidFocusBehaviour
└── MDTextFieldTrailingIcon
    icon: trailing_icon property
    callback: emulated clickable area in on_touch_down()
```

Responsibilities:

- optional trailing icon/callback
- password mask toggling
- Android dialog repositioning when the software keyboard would cover the focused field
- dialog position reset after focus leaves all text fields

### InputField

Source: `gui/widgets/input_field.py`

```text
InputField: FocusableTextField
├── MDTextFieldLeadingIcon
│   icon: supplied icon
├── MDTextFieldHelperText
│   mode: on_error
│   # exposed as error_widget
└── MDTextFieldHintText
    text: title

mode: outlined
optional password mask: •
optional trailing icon/callback
```

`InputField` is the standard editable field used in the login, create-vault, add-account, rename-vault, and change-password dialogs.

## Read-only/detail-field family

Source: `gui/widgets/ro_text_field.py`

### ReadOnlyTextField

```text
ReadOnlyTextField: MDBoxLayout [horizontal]
├── FocusableTextField
│   ├── MDTextFieldLeadingIcon
│   ├── text
│   └── readonly: True
└── MDIconButton
    icon: content-copy
    action: copy field text
```

The copy button remains visible but is disabled/half-opacity if no callback exists.

### PasswordReadOnlyText

```text
PasswordReadOnlyText: ReadOnlyTextField
└── field
    password: True in view mode
    trailing icon: eye / eye-off
```

Entering edit mode also removes masking.

### TotpReadOnlyTextField

```text
TotpReadOnlyTextField: ReadOnlyTextField
└── copy button has two modes
    ├── primary: content-copy → copy only six-digit TOTP
    └── secondary: custom icon (qrcode) → TOTP setup action
```

The account dialog switches between those modes when entering/leaving modification mode.

## Top bars

Source: `gui/widgets/top_bar.py`

### TopBar

```text
TopBar: MDTopAppBar(type="small")
├── MDTopAppBarLeadingButtonContainer
├── MDTopAppBarTitle
│   text: title
│   font_size: 17sp
└── MDTopAppBarTrailingButtonContainer
```

### SettingsScreenTopBar

```text
SettingsScreenTopBar: TopBar(title="Settings")
└── leading container
    └── MDActionTopAppBarButton(icon="arrow-left")
```

## Welcome-screen cards

Source: `gui/widgets/welcome_screen/card_widgets.py`

### DecorativeCard

```text
DecorativeCard: MDCard
orientation: vertical
style: elevated
spacing: 8dp
padding: 24dp
fixed size_hint
hover: disabled
ripple: disabled
```

It bypasses `MDCard`'s button-style touch handling so embedded buttons receive touches normally.

### NoVaultWidget

```text
NoVaultWidget: DecorativeCard(320dp × 190dp)
├── title: "Set up your vault"
├── spacer: 16dp
├── filled button: "Create Vault"
└── text button: "Import Vault"
```

### OpenVaultWidget

```text
OpenVaultWidget: DecorativeCard(320dp × 150dp)
├── title: "Welcome Back!"
├── spacer: 10dp
└── filled button: "Open Vault"
```

## Account list

Source: `gui/widgets/vault_screen/account_list.py`

### AccountEntry

```text
AccountEntry: MDListItem
├── leading icon: account
├── headline: website
└── supporting text: username
```

`website`, `username`, and `on_click_callback` are Kivy properties, allowing displayed values to react to changes.

### AccountList

```text
AccountList: MDRecycleView
└── MDRecycleBoxLayout
    orientation: vertical
    row height: 72dp
    spacing: 8dp
    padding: 4dp
    viewclass: AccountEntry
```

Provides helpers to add, update, and remove rows by `(website, username)`.

## SearchBar

Source: `gui/widgets/vault_screen/search_bar.py`

```text
SearchBar: MDSearchBar
├── normal bar
│   ├── leading container/icon
│   └── trailing container/icon
├── expanded search controls
│   ├── leading arrow-left
│   └── trailing window-close
└── MDSearchViewContainer
    └── MDRecycleView
        └── MDRecycleBoxLayout
            viewclass selected from each result dict
```

`detach()` removes KivyMD's internally attached search-view widget before the top bar itself is replaced.

## PlusButton

Source: `gui/widgets/plus_button.py`

```text
PlusButton: MDFabButton
icon: plus
pos_hint: {right: 0.95, y: 0.05}
```

Used as the vault screen's floating add-account action.

## VaultContextMenu

Source: `gui/widgets/vault_screen/vault_context_menu.py`

```text
VaultContextMenu: MDDropdownMenu
caller: dots-vertical button
hor_growth: left
ver_growth: down
items:
    - Settings
    - Rename
    - Change Password
    - Export
    - Delete
```

Each action dismisses the menu before calling its screen callback.

## Settings widgets

Sources: `gui/widgets/settings_screen/*`

### SettingSection

```text
SettingSection: MDBoxLayout [vertical]
├── title MDLabel
└── MDDivider
```

### SwitchSetting

```text
SwitchSetting: MDBoxLayout(height=56dp)
├── MDLabel(title)
└── MDSwitch
```

### LargeHitBoxSlider

```text
LargeHitBoxSlider: MDSlider
├── MDSliderHandle
└── MDSliderValueLabel
step: 1
height: 48dp
extra vertical hitbox: 12dp
```

### SliderSetting

```text
SliderSetting: MDBoxLayout [vertical]
├── MDLabel("<title>: <value>")
└── LargeHitBoxSlider(min, max, value)
```

### TextSetting

```text
TextSetting: MDBoxLayout [vertical]
├── MDLabel(title)
└── MDTextField(mode="outlined")
```

An optional cleanup callback can normalize text before storing it.

### ChoiceSetting / ChoiceMenu

```text
ChoiceSetting: MDBoxLayout(height=56dp)
├── MDLabel(title)
└── MDButton [text=current value]
    └── ChoiceMenu: MDDropdownMenu
        items: one per allowed value
        hor_growth: left
        ver_growth: up
```

### SettingsMenu

```text
SettingsMenu: MDScrollView
└── content: MDBoxLayout [vertical]
    └── generated SettingSection + setting widgets
```

The widget type is selected from the Python value type/key. See [`SETTINGS_SCREEN.md`](SETTINGS_SCREEN.md).

## File picker abstraction

Sources:

- `gui/widgets/welcome_screen/file_picker.py`
- `gui/widgets/welcome_screen/import_picker.py`
- `gui/widgets/vault_screen/export_picker.py`

`FilePicker` is a controller-like helper rather than a Kivy widget itself.

```text
FilePicker
├── open()
│   ├── Desktop → MDFileManager.show(home)
│   └── Android → native picker intent
├── close()
├── Android activity-result handling
└── ErrorDialog on picker/copy errors
```

### ImportFilePicker

```text
ImportFilePicker: FilePicker
├── type=".vault"
│   ├── Desktop filter: .vault
│   └── Android picker MIME: */*
└── type="picture"
    ├── Desktop filters: png/jpg/jpeg/bmp/webp
    └── Android picker MIME: image/*
```

Selected files are copied into the private app-data directory before the completion callback runs.

### ExportFilePicker

```text
ExportFilePicker: FilePicker
├── final vault synchronization under sync_lock
├── Desktop: folder-selecting MDFileManager
└── Android: ACTION_OPEN_DOCUMENT_TREE
```

## Labels

Source: `gui/widgets/labels.py`

```text
NoAccountsLabel: MDLabel
    text: "Accounts will appear here."
    alignment: centered

NoVaultsLabel: MDLabel
    text: "Imported/Created vaults will appear here."
    alignment: centered
```

`NoAccountsLabel` is used by the current `VaultScreen`. `NoVaultsLabel` remains defined, but the current welcome screen uses `NoVaultWidget` instead.
