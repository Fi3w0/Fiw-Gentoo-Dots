# Refresh selected preferences

Run capture from the repository to update its saved preferences from your
current home. Select only the part you changed:

```sh
python3 tools/capture.py --list
python3 tools/capture.py --config kde-shortcuts
python3 tools/capture.py --config kde-style
python3 tools/capture.py --config fish kitty neovim
python3 tools/capture.py --config ark gwenview prism
```

Each selection reads only its own source files and updates only its config
folder. Missing source files leave the existing capture intact. Shortcuts and
styling remain separate, including their patches for shared KDE files.
`--apps-only` remains a shortcut for Ark, Gwenview and Prism. Running without
a selection refreshes the whole supported preference allowlist.

Fastfetch retains its layout with the built-in Gentoo logo. Kitty keeps
automatic display selection. Neovim capture retains loading of the bundled
theme. VS Code captures explicit preference keys, excluding machine-specific
Java runtimes and unrelated settings. VS Code and Fastfetch sources may use
JSON comments and trailing commas; the saved captures use ordinary JSON.
KDE's device IDs and personal paths are filtered as before.

Fonts and editor theme snapshots are maintained as pinned assets, rather than
recaptured from local plugin directories. Their licences and fingerprints
are documented in [asset credits](assets.md). A preferences-only capture
does not require rebuilding the TUI.

Capture changes the repository files. It does not apply anything to your
desktop. Review before committing:

```sh
git diff -- configs
python3 tools/check-private.py
```

After changing shortcuts, also regenerate their readable reference:

```sh
python3 tools/shortcuts.py
```

Use `--home PATH` to capture from another explicit home directory. Accounts,
sessions and complete application profiles are outside the capture scope.
