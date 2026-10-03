# Copyright 2026 Fiw
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DESCRIPTION="CachyOS Proton Steam Linux Runtime compatibility tool (upstream binary)"
HOMEPAGE="https://github.com/CachyOS/proton-cachyos"
SRC_URI="https://github.com/CachyOS/proton-cachyos/releases/download/cachyos-11.0-20260703-slr/proton-cachyos-11.0-20260703-slr-x86_64.tar.xz"
S="${WORKDIR}/proton-cachyos-11.0-20260703-slr-x86_64"

LICENSE="BSD GPL-2+ LGPL-2.1+ MIT"
SLOT="0"
KEYWORDS="amd64"
RESTRICT="mirror strip"
QA_PREBUILT="*"

src_install() {
	dodir /usr/share/steam/compatibilitytools.d/proton-cachyos-slr
	cp -a -- "${S}/." "${ED}/usr/share/steam/compatibilitytools.d/proton-cachyos-slr/" || die
}

pkg_postinst() {
	einfo "Steam users can link this tool into ~/.local/share/Steam/compatibilitytools.d/proton-cachyos-slr."
	einfo "Restart Steam after adding the link so it detects Proton-CachyOS."
}
