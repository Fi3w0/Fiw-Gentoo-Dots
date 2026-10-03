# Styling assets

The captured styling uses a small subset of the original installed assets:

- Utterly-Round-Dark window decorations retain the original author metadata
  and GPL notice in their captured theme folder.
- Qogir cursors are included as Fiw-Qogir, with the original COPYING file;
  the large unrelated Qogir icon collection is not bundled.
- GentooPurple is derived from Breeze Dark and retains its SPDX copyright
  and LGPL-2.0-or-later notices.
- Four JetBrainsMono Nerd Font Mono styles are captured from the official
  Nerd Fonts v3.5.1 tree with OFL.txt stored as LICENSE-OFL.txt:
  https://github.com/ryanoasis/nerd-fonts/tree/v3.5.1/patched-fonts/JetBrainsMono/Ligatures
- Vesktop's Midnight background customization uses a vendored CSS build from
  refact0r/midnight-discord at commit 85dd67148cbbbfa027cb091e41a479a16ab16a65.
  Its MIT licence is included alongside the theme. Public image/font URLs
  within that upstream theme remain upstream references.

The privacy scanner permits email attribution only in fingerprinted original
theme metadata and colour-scheme notices. It still scans those files for
other private-data patterns. A changed fingerprint requires review before
updating tools/public-attribution.json. The fingerprinted upstream kernel
patch similarly retains public source/test data rather than being rewritten.

## Distribution logos

The user-supplied Gentoo and Arch images are kept in `assets/images`. The
Gentoo image is used in the README; the Arch image is retained as supplied.
These distribution marks are separate from this project's original MIT code.
Upstream references: [Gentoo artwork](https://www.gentoo.org/inside-gentoo/artwork/)
and [name/logo guidelines](https://www.gentoo.org/inside-gentoo/foundation/name-logo-guidelines.html);
[Arch artwork](https://archlinux.org/art/) and
[trademark policy](https://terms.archlinux.org/docs/trademark-policy/).
