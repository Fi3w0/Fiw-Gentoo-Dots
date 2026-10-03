# Confirmed choices — 2026-10-03

Name: **Fiw-Gentoo-Dots**. A stable personal restoration repo, mainly for
Fiw's devices. Start with KDE adjustments/keybinds, categorized package lists
and application preferences. Other desktops and a large module framework
are lower priorities.

- Package sections: kde, fiw-apps, cli, dev, gaming, system, fiw-tools.
  TideWM and its supporting packages are a separate optional section.
- KDE applications such as Dolphin, Ark, Gwenview and Spectacle are in
  fiw-apps. Filelight is optional. Sober is a gaming Flatpak.
- Plasma Login Manager is the default greeter for systemd installations.
- Btrfs tools are optional for Btrfs; ext4 is supported.
- Limine and GRUB are optional, separate bootloader variants. Keep the
  existing loader by default; kernel choice is independent.
- KDE appearance covers colours, fonts and window/app styling. Panels,
  widgets and wallpapers are excluded from the first preset.
- Capture all current functional shortcut assignments, including disabled
  defaults. Recreate their helpers and launchers without fixed host paths.
- Application autostart is an independent optional preset.
- Every application's config is independently optional. Portable Fish,
  Kitty and Neovim configs preserve style without depending on KDE/KWin.
- Fastfetch keeps the layout and colours with a Gentoo logo, replacing the
  personal custom image.
- Include optional MangoHud and Vesktop preferences. Spotify stays stock;
  retain its customization script as an explicit optional step with the
  requested risk/endorsement note. Firefox-Privacy is an optional step.
- **Stock** prefers binaries with Fastfetch, jq and zip deliberately compiled.
  **Fiw's Ryzen** preserves the current tuned Zen 5 setup and uses the custom
  kernel plus a generic binary fallback. Kernel and matching modules compile.
- For additional packages needing source builds, ask compile or skip and
  recommend compilation. Report skipped packages and incomplete features.
- Bubble Tea terminal interface: preset, checkboxes, final preview.
- Ask on existing config conflicts; back up replacements. On updates, keep
  local edits and write proposed changes to `.new` for review.

Original code and configs use MIT; third-party licences remain intact.

Open: fresh installation validation, own-project packaging,
automatic fonts/theme setup, and target-specific boot deployment. Publication
has not been requested. Continue discussing substantial choices with Fiw
before expanding the scope.
