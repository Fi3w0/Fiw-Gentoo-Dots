# Optional bootloader choices

`keep` is the default. `limine` and `grub` select separate package lists.
The draft does not install firmware entries or replace the active bootloader.
Target-specific deployment still needs implementation and a reviewed target
ESP/root layout. Selecting a kernel does not select a bootloader.

GRUB integration must use the target system's installkernel configuration
and generate that system's grub.cfg. Limine integration must derive root and
ESP identifiers on the target and produce the selected custom/generic entries.
Fiw's current dual-boot paths and UUIDs do not belong in generic templates.

The retained `optional/fiw-limine-splice` refreshes the Gentoo block in an
existing Limine configuration and preserves other entries. It is specific
to the current marker/snippet design and is not installed by the default
rice preset or by the GRUB variant.

`optional/fiw-cachy-patch` supports the custom kernel, not a bootloader. It
generates a CachyOS patch and updates the version guard/name. It requires
root and matching upstream source releases; review before running.
