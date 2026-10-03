# Release snapshots

## v0.1.2 — Editor themes and device selections

Neovim's optional config now includes the pinned Catppuccin runtime, and
VS Code includes the ayu MiDas 1.1.0 colour-theme extension. Both retain
upstream licences and work without fetching their themes during installation.
Neovim keeps the captured transparent purple highlights and its fallback.

The final TUI preview adds **n** to save a named device selection. Saved
devices appear on the preset screen, retaining their build profile and
package/config choices. Files stay under ignored `local/devices`.
CLI `--device`, `--save-device` and `--list-devices` support the same workflow.
Selective capture now accepts `--config` for one or several presets, with
`--list` showing supported selections. VS Code capture uses explicit
preference keys and omits machine-specific Java runtimes.

The matching prebuilt TUI is included in the
[tag](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots/src/tag/v0.1.2) and
[source archive](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots/archive/v0.1.2.tar.gz).
See [device presets](devices.md), [recapture](capture.md) and
[app config scope](app-configs.md).

## v0.1.1 — Config update review

Adds **e** for config updates and **p** for pending changes in the final TUI
preview. Each pending file has a diff and an acceptance prompt. Accepting
backs up the current file and rechecks that it has not changed since the
proposal was created. Manually edited proposals remain local preferences
on future updates. Selected patches for shared KDE files produce one combined
proposal containing both styling and shortcut adjustments.

```sh
git clone --branch v0.1.1 https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots.git
cd Fiw-Gentoo-Dots
./install
```

The matching prebuilt Linux amd64 TUI is included in the
[tag](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots/src/tag/v0.1.1) and
[source archive](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots/archive/v0.1.1.tar.gz).
See [config updates](updates.md) for the review flow and CLI commands.

## v0.1.0 — First restoration snapshot

This tag captures the current KDE shortcuts and appearance, categorized
packages, individually optional app preferences and restoration interface.
Use the snapshot when restoring another device:

```sh
git clone --branch v0.1.0 https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots.git
cd Fiw-Gentoo-Dots
./install
```

The repository includes a compressed, static Linux amd64 TUI binary. The
launcher verifies its archive, executable and frontend source fingerprints
before use, then caches the executable in ignored `build/`. Git and Python
3.11+ are sufficient for the bundled TUI. The Python backend remains readable
and runs directly for CLI commands.

Downloads are available through the Forgejo
[tag](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots/src/tag/v0.1.0) and
[source archive](https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots/archive/v0.1.0.tar.gz).
The archive includes the binary, checksums and upstream licence notices.
This is a Git-tagged snapshot; no separate Forgejo release attachment is needed.

Included in this snapshot:

- Exact personal KDE shortcut assignments and optional KDE/GTK styling.
- Stock and Fiw's Ryzen presets with categorized packages and binary preference.
- Independent app configs, user Flatpaks and optional service selections.
- Config requirements, conflict prompts, backup restoration and combined reports.
- Optional Limine/GRUB deployment with target preview and firmware choices.
- A refreshed optional TideWM recipe and an audit covering all current explicit selections.

The installer starts from an existing Gentoo system. Boot automation covers
unsigned amd64 UEFI and plain ext4/Btrfs roots. A full fresh-system package and
boot run remains unverified. TideWM is a live source package, separately
optional and subject to the compile-or-skip prompt.

## Source fallback and maintenance

Go 1.24+ is needed when the binary is absent, unsupported on the current
architecture, or does not match changed frontend source. To explicitly build:

```sh
FIW_DOTS_SOURCE=1 ./install
```

The source fallback does not download a newer Go toolchain automatically.
Config-only changes retain the frontend fingerprint, so recapturing app
preferences does not require rebuilding the binary.

Before tagging a new snapshot, update `VERSION` and rebuild the bundle:

```sh
python3 tools/build-release.py
python3 tools/check-private.py
```

The maintainer build uses `CGO_ENABLED=0`, generic amd64 instructions,
`-trimpath` and no Git build metadata. It records archive/executable/source
SHA256 fingerprints and retains notices for the Go dependencies used in
that binary and for the Go runtime. Review and commit the generated
`assets/bin/` files with the matching frontend source, then tag that commit.
