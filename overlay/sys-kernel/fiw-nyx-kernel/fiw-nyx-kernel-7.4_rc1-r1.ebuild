# Copyright 2026 Fiw
# Distributed under the terms of the GNU General Public License v2

# Fiw's Nyx kernel, release-candidate variant: CachyOS's rc source tree
# (github.com/CachyOS/linux, tag cachyos-7.4-rc1-1) built the Gentoo
# distribution-kernel way.
#
# Differences from the stable fiw-nyx-kernel ebuilds:
#  - no Gentoo patchset (Gentoo publishes the 7.4 one after 7.4 is out);
#  - the 7.3.1 Fedora config as the base, olddefconfig fills in the new
#    7.4 options with their defaults;
#  - EXTRAVERSION (-rc1) stays in the Makefile, because the dist-kernel
#    eclasses expect kernel.release to start with 7.4.0-rc1.
# uname -r -> 7.4.0-rc1-fiw-nyx-v1.2 (name from /etc/kernel/config.d).
#
# Version: fiw-nyx-kernel-7.4_rcN-rM  ->  tag cachyos-7.4-rcN-M
# KEYWORDS is empty on purpose: rc kernels are opt-in only
# (package.accept_keywords: =sys-kernel/fiw-nyx-kernel-7.4_rc* **).

EAPI=8

KERNEL_IUSE_GENERIC_UKI=1

inherit kernel-build toolchain-funcs

MY_PV=${PV/_/-}                       # 7.4_rc1 -> 7.4-rc1
CACHY_TAG=cachyos-${MY_PV}-${PR#r}    # cachyos-7.4-rc1-1
CONFIG_VER=7.3.1-gentoo
GENTOO_CONFIG_P=gentoo-kernel-config-g19

DESCRIPTION="CachyOS-patched Linux kernel built the Gentoo dist-kernel way (Nyx, rc)"
HOMEPAGE="
	https://github.com/CachyOS/linux
	https://wiki.gentoo.org/wiki/Project:Distribution_Kernel
"
SRC_URI+="
	https://github.com/CachyOS/linux/releases/download/${CACHY_TAG}/${CACHY_TAG}.tar.gz
	https://gitweb.gentoo.org/proj/dist-kernel/gentoo-kernel-config.git/snapshot/${GENTOO_CONFIG_P}.tar.bz2
	https://distfiles.gentoo.org/pub/proj/dist-kernel/config/fedora-kernel-config-${CONFIG_VER}.tar.xz
"
S=${WORKDIR}/${CACHY_TAG}

KEYWORDS=""
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
	[[ ${PR} == r0 ]] && die "Name the revision after the CachyOS release: ${PN}-${PV}-r<N> = ${CACHY_TAG%-*}-<N>"
	grep -qx "PATCHLEVEL = $(ver_cut 2)" Makefile || die "${CACHY_TAG} is not ${PV}"
	grep -qx "EXTRAVERSION = -${PV#*_}" Makefile || die "${CACHY_TAG} is not ${PV}"

	# Your own patches from /etc/portage/patches (eapply_user).
	default

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
