# Optional bootloader deployment

`keep` is the default. Limine and GRUB have separate package choices; kernel
selection remains independent. Selecting a loader does not itself deploy it.
Use the final preview's **b** action or include it in **r** full restore.

## Preview and apply

```sh
./install --selection local/selection.json --boot-plan
sudo ./install --selection local/selection.json --deploy-bootloader
# Specify a mounted ESP when automatic discovery does not find yours:
sudo ./install --selection local/selection.json --deploy-bootloader --esp /boot/efi
```

Discovery checks mounted `/efi`, `/boot/efi` and `/boot` candidates for the GPT
ESP type and FAT filesystem. The plan shows the selected partition, root
filesystem, kernel arguments, installed kernel/initramfs candidates and
proposed loader config or commands. UUIDs are derived on the target and kept
in its local state; they are not shipped in the repo.

Firmware registration has three choices:

| Choice | Effect |
|---|---|
| keep | Leave current firmware entries and BootOrder unchanged |
| add | Create an entry without adding it to BootOrder |
| default | Register the selected loader first in BootOrder |

The final deployment confirmation follows the target and firmware preview.
Existing matching firmware entries are reused when their partition and EFI
path match. Other entries are retained. No reboot is performed.

## Limine

The loader goes to `EFI/Fiw-Gentoo/BOOTX64.EFI`, with `limine.conf` beside it.
Versioned kernels and initramfs files are copied below that directory so
Limine can read them from the ESP. Custom Fiw/Cachy kernels appear first,
followed by generic kernels, including an installed binary fallback.

A marked block contains the generated Gentoo entries. Entries outside that
block are preserved. Locally edited managed entries receive a `.new` proposal
instead of being overwritten. ESP free space is checked before copying kernel
artifacts. The protocol and paths follow the upstream
[Limine configuration reference](https://github.com/limine-bootloader/limine/blob/v12.x/CONFIG.md).

## GRUB

`grub-install` uses `--target=x86_64-efi`, a dedicated `Fiw-Gentoo` EFI ID,
`/boot/fiw-gentoo` as its boot directory and `--no-nvram`. Firmware changes are
handled separately by the selected registration choice.

The generated menu lives in `/boot/fiw-gentoo/grub/grub.cfg`. A temporary output
is generated before replacing it. If the previous menu was edited locally,
the new menu becomes a `.new` proposal. Existing `/etc/default/grub` settings
are used by `grub-mkconfig`.

## Kernel updates and backups

Deployment installs a standalone refresh helper at
`/usr/local/libexec/fiw-dots-boot`, a systemd kernel-install hook and a
traditional Gentoo installkernel post-install hook. The active installkernel
configuration uses the compat layout and Dracut. Missing initramfs files are
generated when needed. Each refresh verifies the ESP is still mounted and
updates only the selected loader's managed menu.

The systemd remove hook excludes the removed kernel from its generated menu.
The legacy post-install hook refreshes after additions. Deployment saves
local boot state under `/etc/fiw-gentoo-dots/boot.json`; backup files and reports
live under `/var/lib/Fiw-Gentoo-Dots`. No existing disk partition is formatted.

Automatic deployment currently supports amd64 UEFI, GPT ESPs, plain ext4/Btrfs
roots and unsigned boot. Encrypted, UKI-only, BIOS and signing workflows can
keep their existing loader. Secure Boot being active stops unsigned deployment
before changes. Full boot execution on a fresh installation remains unverified.

`optional/fiw-cachy-patch` refreshes the custom kernel patch; it does not select
a bootloader. See the [helper list](scripts.md) before using it.
