# Restore the setup

Start with an installed amd64 Gentoo system using systemd and a multilib
Plasma profile, with Git and Python 3.11+ available. The snapshot includes a
prebuilt Linux amd64 TUI; Go 1.24+ is needed for its source fallback only.
This repo does not partition disks or install a stage3.

## Terminal interface

Run `./install`. Choose a preset, package sections, individual configs,
kernel/bootloader options, Flatpaks and optional services. Previous selections
are loaded from the ignored `local/selection.json`; press Esc to return to
preset selection when you want to change profiles.

At the final preview:

| Key | Action |
|---|---|
| Enter / s | Save the selection without applying it |
| r | Full restore: packages, Flatpaks, services, configs, selected bootloader |
| i | Install Portage packages |
| f | Install selected user Flatpaks |
| v | Enable selected services |
| a | Restore selected user configs |
| b | Preview and deploy the selected bootloader |
| u | Browse, preview and restore a user config backup |

Full restore checks the KDE session before making package changes. Log out of
Plasma and run from a TTY when KDE configs are selected. Each operation also
has a command for resuming a saved selection:

```sh
./install --selection local/selection.json --plan
sudo ./install --selection local/selection.json --install-packages
./install --selection local/selection.json --install-flatpaks
sudo ./install --selection local/selection.json --enable-services
./install --selection local/selection.json --enable-services
./install --selection local/selection.json --apply-configs
sudo ./install --selection local/selection.json --deploy-bootloader
```

The root service command handles system services; the regular-user command
handles PipeWire units. User Flatpaks and user configs are never applied as root.
Every apply action finishes with a [combined report](reports.md), including
skipped/missing packages and manual setup. Cancellation stops the full restore
sequence and records the completed earlier steps.

## Packages and repositories

Existing GURU and steam-overlay checkouts are reused. Missing overlays needed
by the selected package sections are cloned into temporary storage before
Portage resolves the plan. Their identity is checked, and they are adopted
under `/var/db/repos` only after confirmation. Existing repository checkouts
are not automatically synced or replaced.

Additional source builds prompt **compile or skip**, with compilation
recommended. Skipping a dependency also skips requested packages needing it.
A package report records requested, skipped and missing packages. There is a
final package confirmation before live Portage configuration changes.

Read-only resolution and an export are available separately:

```sh
./install --selection local/selection.json --check-packages
./install --selection local/selection.json --export local/stage
```

The check may download a missing overlay into its temporary root; it does not
register that checkout or change the live Portage configuration. The export
contains proposed files and a plan, not a ready-to-merge repository checkout.

Plasma Login Manager is enabled for selected KDE installs. The installer does
not restart the running greeter, reboot or power off.

## Flatpaks and services

LocalSend (`fiw-apps`) and Sober (`gaming`) have individual Flatpak checkboxes.
Both start unchecked. Selecting them ensures Flatpak is in the package plan;
the separate Flatpak action adds Flathub for the user if absent and installs
only missing selected apps. Existing user installations are kept. Failures
and skips are reported.

Audio, NetworkManager, Bluetooth and power profiles have independent service
checkboxes, also initially unchecked. Their required packages are added when
needed. Enabling a service schedules it for the next boot or user login; the
workflow does not start, stop or restart services. Missing units are reported.
Docker remains a separate choice outside this service preset.

## Configs and updates

Every config is optional and independent of package installation groups.
The separate fonts config includes four JetBrainsMono Nerd Font Mono styles.
Vesktop's Midnight CSS is included with a fixed upstream snapshot. See the
[KDE styling reference](kde-style.md) and [shortcut list](shortcuts.md).
Ark, Gwenview and Prism also have individually optional preferences. Their
capture scope and the preview's package requirements are described in
[app configs](app-configs.md). r2modman setup remains a manual step.

Review Git changes before pulling updates, then restore your saved selection:

```sh
./install --selection local/selection.json --apply-configs --update
```

Locally edited configs remain intact; proposed changes are written to `.new`
files. Replacements receive backups. Root Portage file conflicts ask before
replacement and receive backups too. Reports and user backups live under
`~/.local/state/Fiw-Gentoo-Dots`; system reports and backups live under
`/var/lib/Fiw-Gentoo-Dots`.
Use the TUI's **u** action to [restore a user config backup](backups.md).

## Fiw tools

The `fiw-tools` section includes FiwNode's binary release and the released
Apdatifier Gentoo widget, alongside OpenDeck and Music Presence. Apdatifier
installs QML/scripts without compilation; source-only dependencies still
require the normal compile/skip choice.

FiwNode uses its default config. Sound libraries and audio device selections
stay local. Copies in `~/.local/bin` can shadow `/usr/bin`; manage old copies
manually when switching to the package. Its daemon starts on demand.

Add Apdatifier through Plasma's **Add Widgets** menu. Installation does not
alter panels. An existing user-installed widget can override the system copy;
manage it with `kpackagetool6`. Its preferences stay local.

## Current scope

Automatic boot deployment supports amd64 UEFI, a mounted GPT ESP, plain ext4
or Btrfs roots, and unsigned boot. See [boot setup](boot.md) for previews,
firmware choices and kernel update integration. Other layouts can keep their
existing loader.

The optional [TideWM recipe](tidewm.md) follows the audited upstream master
branch and uses the normal compile-or-skip prompt. End-to-end package and
boot execution on a fresh Gentoo
installation remains unverified; development checks used temporary homes,
staged Portage configuration and mocked system commands.

Do not publish the private original fiw-gentoo archive. It has different
history and host-specific files.
