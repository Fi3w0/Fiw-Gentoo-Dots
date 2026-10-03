# Copyright 2026 Fiw
# Distributed under the terms of the GNU General Public License v2

EAPI=8

inherit unpacker xdg

DESCRIPTION="Discord music status that works with any media player"
HOMEPAGE="https://github.com/ungive/discord-music-presence"
SRC_URI="https://github.com/ungive/discord-music-presence/releases/download/v${PV}/musicpresence-${PV}-linux-x86_64.deb"
S="${WORKDIR}"

LICENSE="music-presence"
SLOT="0"
KEYWORDS="amd64"
RESTRICT="mirror strip bindist"

# Bundles its own Qt; these are the system libs it links against.
RDEPEND="
	app-crypt/mit-krb5
	dev-libs/glib:2
	dev-libs/icu
	media-libs/fontconfig
	media-libs/freetype
	media-libs/libglvnd
	sys-apps/dbus
	x11-libs/libX11
	x11-libs/libxcb
	x11-libs/libxkbcommon
"

QA_PREBUILT="*"

src_install() {
	rm -rf usr/lib || die
	cp -a usr "${ED}/" || die
}
