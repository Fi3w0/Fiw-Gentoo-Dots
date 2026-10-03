# Copyright 2026 Fiw
# Distributed under the terms of the GNU General Public License v2

EAPI=8

inherit unpacker udev xdg

DESCRIPTION="Stream controller (Stream Deck) software, native Linux build"
HOMEPAGE="https://github.com/nekename/OpenDeck"
SRC_URI="https://github.com/nekename/OpenDeck/releases/download/v${PV}/opendeck_${PV}_amd64.deb"
S="${WORKDIR}"

LICENSE="GPL-3+"
SLOT="0"
KEYWORDS="amd64"
RESTRICT="mirror strip"

RDEPEND="
	dev-libs/libayatana-appindicator
	net-libs/webkit-gtk:4.1
"

QA_PREBUILT="*"

src_install() {
	cp -a usr "${ED}/" || die
	if [[ -f etc/udev/rules.d/40-streamdeck.rules ]]; then
		udev_dorules etc/udev/rules.d/40-streamdeck.rules
	fi
}

pkg_postinst() {
	udev_reload
	xdg_pkg_postinst
}

pkg_postrm() {
	udev_reload
	xdg_pkg_postrm
}
