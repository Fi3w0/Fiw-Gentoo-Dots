# Copyright 2026 Fiw
# Distributed under the terms of the GNU General Public License v2

# Fiw's Nyx kernel: CachyOS's released source tree (github.com/CachyOS/linux)
# built the Gentoo distribution-kernel way: Gentoo's patchset and Fedora +
# Gentoo base config, then /etc/kernel/config.d (CachyOS options, own
# tweaks, the -fiw-nyx-vN name), installed through installkernel.
#
# Version = kernel version, revision = CachyOS release:
#   fiw-nyx-kernel-7.2.11-r1  ->  tag cachyos-7.2.11-1
# fiw-nyx-bump adds new versions when CachyOS releases them.
# Based on sys-kernel/gentoo-kernel (amd64 only).

EAPI=8

KERNEL_IUSE_GENERIC_UKI=1

inherit kernel-build toolchain-funcs

CACHY_TAG=cachyos-${PV}-${PR#r}
PATCHSET=linux-gentoo-patches-7.3.1
CONFIG_VER=7.3.1-gentoo
GENTOO_CONFIG_P=gentoo-kernel-config-g19

DESCRIPTION="CachyOS-patched Linux kernel built the Gentoo dist-kernel way (Nyx)"
HOMEPAGE="
	https://github.com/CachyOS/linux
	https://wiki.gentoo.org/wiki/Project:Distribution_Kernel
"
SRC_URI+="
	https://github.com/CachyOS/linux/releases/download/${CACHY_TAG}/${CACHY_TAG}.tar.gz
	https://distfiles.gentoo.org/pub/proj/dist-kernel/patchsets/7.3/${PATCHSET}.tar.xz
	https://gitweb.gentoo.org/proj/dist-kernel/gentoo-kernel-config.git/snapshot/${GENTOO_CONFIG_P}.tar.bz2
	https://distfiles.gentoo.org/pub/proj/dist-kernel/config/fedora-kernel-config-${CONFIG_VER}.tar.xz
"
S=${WORKDIR}/${CACHY_TAG}

KEYWORDS="~amd64"
IUSE="+debug"

BDEPEND="
	debug? ( dev-util/pahole )
"
PDEPEND="
	>=virtual/dist-kernel-${PV}
"

QA_FLAGS_IGNORED="
	usr/src/linux-.*/scripts/gcc-plugins/.*.so
	usr/src/linux-.*/vmlinux
"

src_prepare() {
	[[ ${PR} == r0 ]] && die "Name the revision after the CachyOS release: ${PN}-${PV}-r<N> = ${PN#*-}-${PV}-<N>"
	grep -qx "SUBLEVEL = $(ver_cut 3)" Makefile || die "${CACHY_TAG} is not ${PV}"

	eapply "${WORKDIR}/${PATCHSET}"
	default

	# The name is only <version>-fiw-nyx-vN (CONFIG_LOCALVERSION from
	# /etc/kernel/config.d), never a CachyOS release or other extras.
	sed -i -e "s:^\(EXTRAVERSION =\).*:\1:" Makefile || die

	cp "${WORKDIR}/fedora-kernel-config-${CONFIG_VER}/kernel-x86_64-fedora.config" .config || die

	# Placeholder name; /etc/kernel/config.d/99-name.config sets the real one.
	echo 'CONFIG_LOCALVERSION="-fiw-nyx"' > "${T}"/version.config || die
	local dist_conf_path="${WORKDIR}/${GENTOO_CONFIG_P}"
	local merge_configs=(
		"${T}"/version.config
		"${dist_conf_path}"/base.config
		"${dist_conf_path}"/6.12+.config
	)
	use debug || merge_configs+=( "${dist_conf_path}"/no-debug.config )
	use secureboot && merge_configs+=(
		"${dist_conf_path}/secureboot.config"
		"${dist_conf_path}/zboot.config"
	)

	kernel-build_merge_configs "${merge_configs[@]}"
}
