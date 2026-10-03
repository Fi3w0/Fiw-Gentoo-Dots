# Helpers and what they do

| Helper | Purpose | How it is used |
|---|---|---|
| `install` | Builds/opens the Bubble Tea chooser, or forwards CLI options to the Python backend | Main entry point |
| `lib/rice.py` | Validates selections, previews plans, restores configs and installs Portage packages | Called by the entry point/TUI |
| `lib/setup.py` | Stages missing overlays, installs selected user Flatpaks and enables selected service units | Called by the backend |
| `lib/boot.py` | Detects the target ESP/root, previews/deploys Limine or GRUB, refreshes kernel menus | Boot action; copied as `fiw-dots-boot` on deployment |
| `fiw-shot` | Captures a region or monitor using Spectacle, copies it to the clipboard and offers Save/Edit through a notification | Installed with KDE shortcuts; `region` or `screen` argument |
| `tools/capture.py` | Recaptures the explicit preference allowlist without copying full personal profiles | Maintenance command; review the diff |
| `tools/shortcuts.py` | Regenerates the readable shortcut reference from captured repo files | Run after changing/capturing shortcuts |
| `tools/check-private.py` | Scans publishable files for personal paths, identifiers and credentials; keeps fingerprinted upstream attribution | Run before committing |
| `optional/fiw-cachy-patch` | Downloads matching vanilla/CachyOS kernel sources, generates a patch and adjusts the installed guard/name config | Explicit manual root operation; not part of ordinary restoration |
| `optional/fiw-limine-splice` | Replaces the old Gentoo snippet block in an existing Limine menu and orders its entries | Explicit manual use with an ESP argument; specific to the earlier snippet design |
| `optional/spotify/spotify-patch` | Runs the retained SpotX/Spicetify customization workflow for the Gentoo Spotify client | Explicit optional user operation; stock Spotify is the default |
| `optional/spotify/spicetify-snapshotfix` | Copies missing Marketplace fragments into the captured Spotify UI snapshot format | Called by the optional customization workflow |

The kernel refresh helper installed on a target runs with `--refresh`. Its
kernel hooks are created only when boot deployment is explicitly confirmed;
they are not enabled by the default `keep` choice.

The older Cachy patch helper predates the snapshot guard shipped by this
repo. It does not update the repo's `snapshot.json`, checksum or version mask;
review/update those together when preparing a new supported kernel snapshot.
It is retained as a reference, not run automatically.

For the optional Spotify scripts, see [the setup and risk note](spotify.md).
Unofficial Spotify modifications are optional and used at your own risk.
This project does not endorse bypassing paid features.
