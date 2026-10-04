# Optional app preferences

Each preset has its own checkbox. Configs can be restored for already installed
apps without selecting a package section. Close the affected app before
restoring its preferences so it reads the new settings on its next launch.

## Additional captured apps

| Preset | Captured preferences | Target file |
|---|---|---|
| Ark | Open the destination after extraction; visible, locked sidebar; hidden status bar | `.config/arkrc` |
| Gwenview | Hidden menu bar and information sidebar splitter proportions | `.config/gwenviewrc` |
| Prism | Breeze appearance, dark Breeze icons, console font/limits, console visibility and launcher/game-time behaviour | `.local/share/PrismLauncher/prismlauncher.cfg` |

These use key-by-key merges. Existing recent files, accounts, Minecraft
instances, machine paths, Java selection, memory limits and unrelated
preferences stay on the target. The Prism path is for the native Gentoo
package. Its Minecraft and Java setup is listed in the final manual steps.

Ark, Gwenview and Prism are selected in both shipped presets and can be
unchecked independently. Recapture only these allowlisted keys with:

```sh
python3 tools/capture.py --apps-only
```

## Config requirements

The final preview lists the packages needed for each selected config:

| Status | Meaning |
|---|---|
| installed | Portage confirms the package is present on this device |
| selected | The package is directly included in the selected package plan |
| missing | The package is absent and is not directly selected |
| unverified | Portage is unavailable, so installation cannot be checked |

Some requirements arrive as dependencies, such as Plasma components through
`plasma-meta`. Their preview status can be missing until Portage resolves and
installs them. Requirements do not automatically check package groups or
block config-only restoration. The combined report checks actual installed
packages again, including requirements of apps whose installation was skipped.

Fish, Kitty, Neovim and Fastfetch have no Plasma or KWin requirements. Fonts
have their own checkbox; Kitty can use its fallback font if those are omitted.
Both Kitty profiles start Fish explicitly, so the Kitty preset requires Fish
even when the optional Fish preferences are unchecked.
For Fish in TTY and SSH logins too, run `chsh -s "$(command -v fish)"` as your
regular user after installing Fish, then log in again.
Neovim's config includes a pinned Catppuccin runtime in its native package
directory and loads it before the captured purple highlights. It needs no
plugin manager or runtime download. A built-in fallback remains available if
the theme files are omitted manually.

VS Code's optional config includes ayu MiDas 1.1.0 as a user colour-theme
extension. Its original theme JSON is bundled with a minimal theme manifest;
it has no JavaScript entry point or development dependencies. This uses the
native VS Code default user and extension locations. Custom extension
directories, named VS Code profiles and other Code variants need their own
locations. Existing theme files use the normal conflict/backup/update flow.

Both editors' theme versions and asset fingerprints are recorded in
`assets/editor-themes.json`; [asset credits](assets.md) retain upstream licences.
VS Code preferences merge selected keys and keep existing unrelated settings,
including Java runtime choices. JSON comments and trailing commas are accepted
when reading existing settings; an accepted merge writes ordinary formatted
JSON. Backups retain the original file, including its comments.

## r2modman

Set its appearance through the app's settings. Global and game settings use a
shared IndexedDB store, as shown in the
[upstream settings implementation](https://github.com/ebkr/r2modmanPlus/blob/a1897e3d6f7c1946dc51312252db1cc25f1dace0/src/r2mm/manager/SettingsDexieStore.ts).
There is no captured r2modman config preset; its Electron profile and databases
remain local. Restore wanted mod profiles through the app's
[profile export/import workflow](https://github.com/ebkr/r2modmanPlus/wiki/Profiles).
Selected gaming installs include this reminder in their combined report.
