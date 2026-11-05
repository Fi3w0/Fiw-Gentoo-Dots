# Copyright 2021-2026 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

# ::fiw copy of virtual/dist-kernel that also accepts sys-kernel/fiw-nyx-kernel,
# so dist-kernel modules (nvidia-drivers) rebuild for the Nyx kernel. Same
# version and revision as the Nyx kernel: a new CachyOS release changes the
# subslot and rebuilds the modules. fiw-nyx-bump keeps them in step.

EAPI=8

DESCRIPTION="Virtual to depend on any Distribution Kernel (incl. fiw-nyx-kernel)"
SLOT="0/${PVR}"
KEYWORDS="~amd64"

RDEPEND="
	|| (
		~sys-kernel/fiw-nyx-kernel-${PV}
		~sys-kernel/gentoo-kernel-${PV}
		~sys-kernel/gentoo-kernel-bin-${PV}
		~sys-kernel/vanilla-kernel-${PV%_p*}
	)
"
