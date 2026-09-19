# Settings Screen

Source: `gui/screens/settings_screen.py`, `gui/widgets/settings_screen/*`, `core/constants.py`

## Screen root

```text
<SettingsScreen>:
    name: "settings"
    md_bg_color: theme.secondaryContainerColor

    main_container: MDBoxLayout
        └── SettingsMenu
```

The shared top-bar slot contains:

```text
SettingsScreenTopBar: TopBar
├── leading button: arrow-left
│   action: back to VaultScreen
└── title: "Settings"
```

## SettingsMenu

`SettingsMenu` is generated from a copy of the current settings dictionary.

```text
SettingsMenu: MDScrollView
    do_scroll_x: False
    do_scroll_y: True

    └── content: MDBoxLayout
        orientation: vertical
        adaptive_height: True
        padding: 16dp
        spacing: 8dp

        ├── SettingSection("Password Generation")
        ├── ... settings ...
        ├── SettingSection("Security")
        ├── ... settings ...
        ├── SettingSection("Others")
        └── ... settings ...
```

A section heading is:

```text
SettingSection: MDBoxLayout
├── MDLabel
│   font_style: Title / large
│   color: theme.primaryColor
└── MDDivider
```

## Current generated settings

The following is the concrete UI produced by the current default/current schema.

```text
Password Generation
├── TextSetting
│   title: "Special chars"
│   value: !"#$%&'()*+,-./:<=>?@[\]^_`{|}~
│   behavior: unsupported chars and duplicates are removed
│
├── SliderSetting
│   title: "Password length"
│   range: 8..128
│   default: 24
│
├── SwitchSetting
│   title: "Use uppercase"
│   default: True
│
├── SwitchSetting
│   title: "Use digits"
│   default: True
│
└── SwitchSetting
    title: "Use special"
    default: True

Security
├── SliderSetting
│   title: "Timeout duration"
│   range: 10..300
│   default: 60
│
└── SwitchSetting
    title: "Lock on minimize"
    default: True

Others
└── ChoiceSetting
    title: "Theme"
    options: ["Light", "Dark"]
    default: "Light"
```

## Setting widget selection rule

```text
value is bool       → SwitchSetting
value is int        → SliderSetting
key == "theme"      → ChoiceSetting
otherwise           → TextSetting
```

Because `bool` is checked before `int`, boolean settings do not accidentally become sliders.

## Setting primitives

```text
SwitchSetting: MDBoxLayout(height=56dp)
├── MDLabel(title)
└── MDSwitch(active=value)

SliderSetting: MDBoxLayout(vertical)
├── MDLabel("<title>: <value>")
└── LargeHitBoxSlider
    ├── MDSliderHandle
    └── MDSliderValueLabel

TextSetting: MDBoxLayout(vertical)
├── MDLabel(title)
└── MDTextField(mode="outlined")

ChoiceSetting: MDBoxLayout(height=56dp)
├── MDLabel(title)
└── MDButton [text]
    └── ChoiceMenu: MDDropdownMenu
        └── one item per option
```

## Persistence lifecycle

Changing a control updates the in-memory `Settings` object immediately and increments the vault change version. Theme changes are also applied immediately.

When the settings screen is left:

```text
on_leave
├── synchronize vault/settings
├── push password-generation configuration into PwdManager
├── apply timeout_duration to app watchdog
└── apply lock_on_minimize to app lifecycle behavior
```
