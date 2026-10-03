# Copyright 2026 Fiw
# Distributed under the terms of the MIT License

EAPI=8

inherit desktop xdg

DESCRIPTION="FiwNode soundboard and virtual microphone for PipeWire"
HOMEPAGE="https://github.com/Fi3w0/FiwNode"
SRC_URI="https://github.com/Fi3w0/FiwNode/releases/download/v${PV}/FiwNode-v${PV}-linux-x86_64.tar.gz"
S="${WORKDIR}/FiwNode-v${PV}-linux-x86_64"

LICENSE="MIT"
SLOT="0"
KEYWORDS="amd64"
RESTRICT="mirror strip"
QA_PREBUILT="usr/bin/*"

RDEPEND="
	>=sys-libs/glibc-2.39
	dev-db/sqlite:3
	dev-qt/qtbase:6[dbus,gui,widgets]
	dev-qt/qtdeclarative:6
	dev-qt/qtsvg:6
	media-video/ffmpeg
	media-video/pipewire
	media-video/wireplumber
"

src_install() {
	dobin bin/fiwnode bin/fiwnode-daemon bin/fiwnode-gui
	domenu assets/dev.fiw.fiwnode.desktop
	doicon -s scalable assets/icons/fiwnode.svg
	doicon -s scalable assets/icons/fiwnode-tray-symbolic.svg
	insinto /usr/share/icons/hicolor/symbolic/apps
	doins assets/icons/fiwnode-tray-symbolic.svg
	dodoc README.md CHANGELOG.md LICENSE
}

pkg_postinst() {
	xdg_pkg_postinst
	elog "FiwNode starts its daemon on demand; no system service is enabled."
	elog "Existing per-user installs in ~/.local/bin can shadow /usr/bin."
	elog "Remove those old binaries manually when you are ready to use this package."
}
