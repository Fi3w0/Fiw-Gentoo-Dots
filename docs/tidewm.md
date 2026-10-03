# Optional TideWM

The `tidewm` section remains unchecked in the shipped presets. It installs
TideWM and its selected Wayland tools without changing KDE config presets.
Its GURU tools trigger repository preparation even when `fiw-apps` and
`gaming` are unchecked.

The live recipe follows upstream `master`, audited at
[f86db8bd](https://github.com/Fi3w0/TideWM/tree/f86db8bd02a7a52de9028bb075fe845717f398f3).
It builds `TideWM`, `tidectl` and the `wavefmt` formatter, with optional
screencast/accessibility features. Rust 1.88 is required by the locked Lua
binding version; the recipe also declares Wayland, pkg-config and the GTK
portal fallback used by the upstream session.

The recipe fetches and vendors Cargo dependencies during unpack, then uses
frozen builds with no compilation-stage network resolution. Screencasting
is enabled by default, including the session-specific portal files.

This is a source build. The main installer shows it as an additional
compile-or-skip choice; it is not part of the deliberately small source list.
A live recipe follows future upstream changes, while the current audit SHA
documents the version reviewed for this snapshot. Compilation of the
refreshed tree on a fresh device remains unverified.

After installation, choose **TideWM** at login. It creates its own default
configuration on first launch. No existing TideWM settings are captured or
overwritten by this repo. Upstream documents its
[configuration format](https://github.com/Fi3w0/TideWM/blob/f86db8bd02a7a52de9028bb075fe845717f398f3/WAVE.md).
