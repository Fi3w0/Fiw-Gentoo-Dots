# Copyright 2026 Fiw
# Distributed under the terms of the GNU General Public License v2

EAPI=8

DESCRIPTION="GloriousEggroll's Proton-GE Steam compatibility tool (upstream binary)"
HOMEPAGE="https://github.com/GloriousEggroll/proton-ge-custom"
SRC_URI="https://github.com/GloriousEggroll/proton-ge-custom/releases/download/GE-Proton11-7/GE-Proton11-7-x86_64.tar.gz"
S="${WORKDIR}/GE-Proton11-7-x86_64"

LICENSE="BSD GPL-2+ LGPL-2.1+ MIT"
SLOT="0"
KEYWORDS="amd64"
RESTRICT="mirror strip"
QA_PREBUILT="*"

src_install() {
	dodir /usr/share/steam/compatibilitytools.d/GE-Proton
	cp -a -- "${S}/." "${ED}/usr/share/steam/compatibilitytools.d/GE-Proton/" || die
}

pkg_postinst() {
	einfo "Steam users can link this tool into ~/.local/share/Steam/compatibilitytools.d/GE-Proton."
	einfo "Restart Steam after adding the link so it detects Proton-GE."
}
