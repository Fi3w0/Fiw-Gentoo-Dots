# Setup and current draft boundaries

Start with an installed amd64 Gentoo system using systemd and a multilib
Plasma profile. This repo does not partition disks or install the stage3.
Plasma Login Manager currently requires systemd. It is the default greeter
when installing the KDE section.

1. Run `./install`, make selections and review the final preview.
2. Save the selection. It lives in the ignored `local/selection.json`.
3. Export for inspection if desired:
   `./install --selection local/selection.json --export local/stage`.
4. Install packages via the TUI or
   `sudo ./install --selection local/selection.json --install-packages`.
   Resolution happens in a temporary Portage config before live files change.
   Missing binaries prompt compile/skip; final installation requires confirmation.
5. Apply user configs as the target user:
   `./install --selection local/selection.json --apply-configs`.
   Log out of Plasma and use a TTY for KDE configs; running KDE can overwrite
   edited config files. Portable app configs can be restored separately.

For updates, review the Git changes, then use the saved selection with
`--apply-configs --update`. There is no automatic git pull or upstream upgrade.
Backups and reports live under `~/.local/state/Fiw-Gentoo-Dots`. Package reports
and system backups live under `/var/lib/Fiw-Gentoo-Dots`.

## Explicit setup steps

Root package installation enables `plasmalogin.service` for selected KDE
installs without restarting the running greeter. After the desired packages
are installed, enable the services you use:

```sh
sudo systemctl enable NetworkManager bluetooth power-profiles-daemon
systemctl --user enable pipewire.socket pipewire-pulse.socket wireplumber.service
```

Docker stays disabled until needed. The installer does not reboot or power off.

Flatpak apps are listed separately. Add Flathub if absent, then install only
the selected categories' apps explicitly, for example:

```sh
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub org.localsend.localsend_app
flatpak install --user flathub org.vinegarhq.Sober
```

The independently selectable `fonts` config includes the four used styles of
JetBrainsMono Nerd Font Mono from the official Nerd Fonts v3.5.1 release,
with its OFL licence. It works with KDE and portable apps alike. The entire
personal font collection is not included. Neovim uses its built-in theme as
a fallback when Catppuccin is not installed. Vesktop's selected Midnight
theme CSS is captured with a fixed upstream snapshot and its MIT licence.

## Fiw tools

The `fiw-tools` section includes FiwNode's x86-64 binary release and the
released Apdatifier Gentoo widget, alongside OpenDeck and Music Presence.
Apdatifier installs QML/scripts without compilation; any dependencies needing
source builds still go through the normal compile/skip prompt.

FiwNode uses its default configuration. The installer does not copy sound
libraries, microphone/output selections or personal app state. Older copies
in `~/.local/bin` can shadow the Portage-installed binaries in `/usr/bin`;
remove those manually when ready to switch. The daemon starts on demand.

Apdatifier is available through Plasma's **Add Widgets** menu. Installing it
does not alter panels. An existing user-installed widget can override the
system copy; use `kpackagetool6` to manage it. Its preferences remain local.

## Remaining work before declaring a fresh install verified

- Run both presets on a fresh Gentoo test installation. Root package execution
  has not been exercised on the working desktop.
- Implement target-specific Limine/GRUB deployment after reviewing the target
  ESP and boot layout. Current variants select packages and provide setup notes.
- Refresh the optional TideWM live ebuild branch/dependency recipe against the
  upstream development version before building it on a new machine.
- Repository sync is an explicit prerequisite when GURU or steam-overlay is
  absent; the draft aborts cleanly on resolution failure rather than guessing.

Do not publish the private original fiw-gentoo repository. It is the working
archive and has different history and host-specific files.
