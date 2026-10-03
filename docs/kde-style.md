# KDE styling preset

Fiw’s current appearance, restored through the optional `kde-style` config.
Dolphin, Spectacle, fonts and portable terminal configs have their own
checkboxes. The settings below describe the capture; no desktop settings
are applied by reading this reference.

## Appearance

| Setting | Captured value |
|---|---|
| Colour scheme | GentooPurple, derived from Breeze Dark |
| Accent / focus | `#6E56AF` |
| Window background | `#1D1929` |
| View background | `#16131F` |
| Normal text | `#E8E4F3` |
| Selection background | `#534183` |
| Icons | Breeze Dark |
| KDE look and feel | Breeze Dark |
| Cursor | Qogir, bundled under the name Fiw-Qogir |
| Window decorations | Utterly-Round-Dark, bundled Aurorae theme |
| Border size | No side borders |
| Decoration tooltips | Disabled |
| Animation duration factor | `0.25` |

The complete colour groups live in
[kdeglobals](../configs/kde-style/kconfig/.config/kdeglobals). Theme and cursor
assets are included in the same config, with their original licence notices.
Breeze and Aurorae come through the normal Plasma package dependencies.
No terminal association is set by the appearance preset.

## Fonts

| Use | Family | Size |
|---|---|---|
| General UI, menus, toolbar and window title | JetBrainsMono Nerd Font Mono | 10 pt |
| Fixed-width text | JetBrainsMono Nerd Font Mono | 10 pt |
| Small readable text | JetBrainsMono Nerd Font Mono | 8 pt |
| Kitty | JetBrainsMono Nerd Font Mono | 11 pt |

KDE uses antialiasing, slight hinting and RGB subpixel rendering as captured.
The separate `fonts` checkbox installs Regular, Bold, Italic and Bold Italic
under the user’s font directory; keep it selected to reproduce this typography
unless the same family is already installed. Fonts work independently of KDE.

## GTK styling

The KDE style checkbox also restores the captured GTK 3 and GTK 4 preferences:

- Dark preference, Breeze Dark icons and the same 10 pt font.
- Fiw-Qogir cursor at size 24.
- GTK 3’s Breeze theme preference.
- The current `gtk.css` imports and generated purple `colors.css` palette.

Other settings in each `settings.ini` are preserved. Existing CSS files follow
the same conflict, backup and update rules as other configs. Applications use
these colours and preferences according to their toolkit’s theme support.

## Dolphin and Spectacle

These are individually optional configs.

| Config | Captured preferences |
|---|---|
| Dolphin | Menu bar hidden; toolbar with back, forward, up, home, location, search and menu; fixed 22 px Places icons; sidebar/dock state; case-insensitive filename filtering |
| Dolphin window rule | 96% active opacity, 92% inactive opacity; applies to Dolphin windows |
| Spectacle | Annotation tool selection; release-to-capture disabled |

The toolbar XML includes the captured app action properties. The sidebar/dock
state is Qt’s saved layout; it does not copy tabs, bookmarks or file history.
KWin rules merge with other target rules instead of replacing their list.

## Portable terminal styling

Fish, Kitty, Neovim and Fastfetch stay separate from KDE settings:

- **Fish:** aliases, Fastfetch greeting and command completion notifications.
- **Kitty:** lavender palette, padding, 50% opacity in the main profile and
  62% in the brighter profile. Display selection is automatic for Wayland/X11;
  blur is used where the compositor supports it.
- **Neovim:** transparent backgrounds and purple highlights; uses an existing
  Catppuccin Mocha plugin when available, otherwise the built-in dark theme.
- **Fastfetch:** the current tree layout and colours, with its built-in Gentoo logo.

## Applying the capture

Select the configs in `./install` and review the preview. They can be restored
without selecting package installation groups, for applications already present.
For KDE configs, log out of Plasma and apply from a TTY so the session cannot
rewrite the files. The installer checks this before making changes.

Configuration conflicts prompt apply or keep. Replacements receive backups;
updates preserve local edits and leave proposed changes in `.new` files.
Panels, widgets, wallpaper and output-specific tiling layouts stay local.
The [shortcut preset](shortcuts.md) separately restores the captured desktop
count and rows, without copying desktop or monitor IDs.
