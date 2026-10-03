# Copyright 2026 Fiw
# Distributed under the terms of the MIT License

EAPI=8

DESCRIPTION="Gentoo/Portage update notifier for KDE Plasma 6"
HOMEPAGE="https://github.com/Fi3w0/apdatifier-gentoo"
SRC_URI="https://github.com/Fi3w0/apdatifier-gentoo/releases/download/v${PV}/apdatifier-gentoo_v${PV}.plasmoid"
S="${WORKDIR}/${P}"

LICENSE="MIT"
SLOT="0"
KEYWORDS="amd64"
RESTRICT="mirror"
BDEPEND="app-arch/unzip"
RDEPEND="
	app-admin/sudo
	app-misc/jq
	app-portage/portage-utils
	dev-libs/libxml2
	dev-qt/qt5compat:6[qml]
	dev-qt/qtbase:6[network]
	dev-vcs/git
	kde-frameworks/kiconthemes:6
	kde-frameworks/kirigami:6
	kde-frameworks/kitemmodels:6
	kde-frameworks/kcmutils:6
	kde-frameworks/knotifications:6
	kde-frameworks/kdeclarative:6
	kde-frameworks/ksvg:6
	kde-plasma/libplasma:6
	kde-plasma/plasma5support:6
	kde-plasma/plasma-workspace:6
	net-misc/curl
"

src_unpack() {
	mkdir -p "${S}" || die
	unzip -q "${DISTDIR}/${A}" -d "${S}" || die
}

src_install() {
	insinto /usr/share/plasma/plasmoids/com.github.fiw.apdatifier-gentoo
	doins metadata.json
	doins -r contents
	fperms +x /usr/share/plasma/plasmoids/com.github.fiw.apdatifier-gentoo/contents/tools/sh/{init,management,terminal,upgrade,utils,widgets}
	dodoc "${FILESDIR}/LICENSE.MIT"
}

pkg_postinst() {
	elog "Add Apdatifier Gentoo through Plasma's Add Widgets menu."
	elog "This package does not change panels or enable scheduled checks."
	elog "A per-user copy can override this system package; manage it with kpackagetool6."
}
