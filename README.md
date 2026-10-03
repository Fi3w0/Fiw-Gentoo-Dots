<div align="center">

# Fiw-Gentoo-Dots

**My Gentoo setup, ready to make home feel like home again.**

![Gentoo](https://img.shields.io/badge/Gentoo-54487A?logo=gentoo&logoColor=white)
![KDE Plasma](https://img.shields.io/badge/KDE_Plasma-1D99F3?logo=kde&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-purple)
![Status](https://img.shields.io/badge/status-work_in_progress-yellow)

[KDE & apps](#configs) · [Shortcuts](docs/shortcuts.md) · [Packages](#package-sections) · [Setup](docs/setup.md)

</div>

---

## Overview

A personal Gentoo rice and restoration kit: my Plasma styling, current
shortcuts, package lists and the app preferences I use every day. Built
mainly for my own devices, with deliberate updates and a preview before
anything is applied.

- **KDE first:** colours, fonts, cursor, window styling and current keybinds.
- **Pick what you want:** package sections and individually optional app configs.
- **Portable terminals:** Fish, Kitty and Neovim work across compositors.
- **Binaries preferred:** a small source list, with a choice before extra builds.
- **Keep your edits:** conflict prompts, backups and `.new` proposals on updates.

**Work in progress:** configuration restoration and the TUI are ready for review.
Package installation needs a supervised first run on a fresh Gentoo system.
The existing installation has not been changed by creating this repo.

## Start

```sh
git clone https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots.git
cd Fiw-Gentoo-Dots
./install
```

The Bubble Tea interface offers a preset, package sections, individual app
configs, kernel/bootloader choices, extras, and a final preview. Enter at the
preview saves a selection without applying it. `a` restores configs; `i`
starts the package installation workflow with sudo. Go 1.24+ builds the TUI;
Python 3.11+ runs the backend. Go dependencies are recorded in go.mod/go.sum.

For a preview without building the TUI:

```sh
./install --plan --profile stock
./install --plan --profile fiw-ryzen
```

See [setup](docs/setup.md) for installation steps and draft limitations.

## Presets

| Preset | Build settings | Kernel |
|---|---|---|
| Stock | Portable compiler settings; binary packages preferred | Generic Gentoo binary kernel |
| Fiw's Ryzen | Current Ryzen 9900X/Zen 5 tuning and NVIDIA configuration | Tested custom kernel plus generic binary fallback |

Both deliberately compile Fastfetch, jq and zip. Custom kernels and their
matching external modules compile when selected. Other packages prefer
Portage binaries or upstream `-bin` packages. Additional source builds
require a compile-or-skip choice, with compilation recommended; skipped
dependencies also cause dependent requested applications to be skipped.

The custom kernel snapshot currently targets 7.2.8 with the tested
CachyOS 7.2.7-1 patch. Refresh it explicitly when updating the snapshot.

## Package sections

| List | Contents |
|---|---|
| [kde](packages/kde.list) | Plasma, Plasma Login Manager, desktop components and supporting fonts |
| [fiw-apps](packages/fiw-apps.list) | Everyday apps including Dolphin, Ark, Gwenview and Spectacle |
| [cli](packages/cli.list) | Shell, terminal utilities and FFmpeg |
| [dev](packages/dev.list) | Languages and development tools |
| [gaming](packages/gaming.list) | Steam, Proton, Prism, MangoHud and r2modman; Sober is in flatpaks/gaming.list |
| [system](packages/system.list) | System utilities; the selected kernels are added by the installer |
| [fiw-tools](packages/fiw-tools.list) | FiwNode binary release, Apdatifier Gentoo, OpenDeck and Music Presence |
| [tidewm](packages/tidewm.list) | Optional compositor and supporting utilities |

Filelight, NVIDIA drivers and Btrfs tools are separate extras. Ext4 does not
require Btrfs tools. LocalSend is an optional Flatpak in the apps section.
Limine and GRUB are optional alternatives; retaining the current loader is
the default. Kernel choice is independent of bootloader choice.

## Configs

Every config is independently selectable, even when its package section is
unchecked—for example, to configure apps already installed. KDE appearance covers colours,
fonts, cursor, window decorations and Dolphin styling. Panels, widgets and
wallpapers are excluded. All portable current shortcut assignments,
including disabled defaults, are captured with their launchers and helpers;
unused machine-specific activity IDs are omitted.

Fish, Kitty and Neovim are usable without KDE or KWin. Fastfetch keeps the
tree layout and purple colours with the built-in Gentoo logo. MangoHud and
Vesktop preferences are included; browser profiles, chat sessions and account
data are excluded. App autostart is a separate optional selection.

Spotify is stock by default. The existing customization scripts remain an
[explicit optional step](docs/spotify.md). [Firefox-Privacy](docs/firefox.md)
is also optional.

Existing differences prompt apply-or-keep and get backups when replaced.
Updates leave locally edited configs intact and write the proposal to `.new`.
KConfig patches preserve unrelated keys and groups; JSON patches preserve
unrelated preferences and login data already on the target device.

## Project layout

```text
cmd/dots/     Bubble Tea selection interface
configs/      Optional KDE and app configs
packages/     Categorized Portage package lists
presets/      Stock and Fiw's Ryzen defaults
portage/      Build settings and binary preferences
overlay/      Selected additional packages
optional/     Kernel, boot and app helpers
flatpaks/     Separate optional Flatpak lists
docs/         Setup, decisions and asset credits
```

## Maintenance

```sh
python3 tools/capture.py       # recapture only the explicit allowlist
python3 tools/check-private.py
python3 -m unittest discover -s tests
go test ./...
```

Review captures before committing. `local/` and built binaries are ignored.
This repo starts with fresh history. Third-party theme/cursor assets retain
their licence notices; overlay ebuilds retain their original notices.

## License

Original code and configuration contributions are licensed under [MIT](LICENSE).
Bundled third-party assets, fonts, patches and ebuilds keep their own licences
and attribution; see [asset credits](docs/assets.md).

---

<div align="center">A personal Gentoo setup by Fiw.</div>
