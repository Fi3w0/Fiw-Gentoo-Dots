# Commands and helpers

| Command/helper | Purpose |
|---|---|
| `./install` | Opens the TUI; CLI options use the same backend. See [setup](setup.md). |
| `tools/capture.py` | Refreshes selected config preferences from your home. See [capture](capture.md). |
| `tools/shortcuts.py` | Regenerates the readable KDE shortcut reference after recapture. |
| `tools/check-private.py` | Checks publishable files for personal paths, identifiers and credentials. |
| `tools/build-release.py` | Rebuilds the bundled TUI, fingerprints and dependency licences. |
| `tools/ci/check.py` | Checks privacy, asset fingerprints, Python syntax and frontend compilation. |
| `tools/ci/mirror.py` | Synchronizes branches/tags to GitHub after checks. See [CI](ci.md). |
| `fiw-shot` | Screenshot region/monitor, copy to clipboard, then offer Save/Edit. Installed with KDE shortcuts. |
| `optional/fiw-cachy-patch` | Manually generates/installs a matching CachyOS kernel patch and updates the installed guard/name. |
| `optional/spotify/spotify-patch` | Runs the optional Spotify customization workflow. |
| `optional/spotify/spicetify-snapshotfix` | Supplies missing Marketplace fragments for that customization. |

The custom-kernel helper does not update the repo's `snapshot.json`, patch
checksum or version mask. Review those together when refreshing the snapshot.

Confirmed boot deployment installs its own refresh helper and kernel hooks.
The default `keep` choice leaves them disabled. See [boot setup](boot.md).

Spotify modifications are optional and at your own risk. This project does
not endorse bypassing paid features. See [Spotify setup](spotify.md).
