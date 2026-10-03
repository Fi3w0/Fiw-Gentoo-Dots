# Named device selections

Choose Stock or Fiw's Ryzen, then adjust packages, app configs, kernel,
bootloader, extras, Flatpaks and services. At the final preview, press **n**
and enter a name such as `desktop` or `portable`. Enter saves the selection.
An existing name asks before replacement, with keeping it as the default.
Saving a preset does not install packages or apply configs.

Launch the TUI again and press Esc to reach the preset screen. Your named
devices appear alongside the two shipped presets. Choosing a saved device
loads its own choices; its underlying Stock/Ryzen build profile is retained.
The most recent selection is still reused on normal startup.

CLI equivalents:

```sh
./install --selection local/selection.json --save-device desktop
./install --profile stock --save-device portable
./install --list-devices
./install --device desktop --plan
./install --device portable --apply-configs
```

Names use 1–48 lowercase letters, digits, hyphens or underscores, beginning
with a letter or digit. Each selection is stored in `local/devices/NAME.json`
with user-only permissions. The folder is ignored by Git. No hostname,
hardware identifiers or filesystem UUIDs are collected. Invalid local files
are omitted from the chooser; explicit CLI loading reports their error.

To reuse a selection on another device, copy the wanted JSON file into that
checkout's `local/devices` folder. Use Stock for portable build settings;
Fiw's Ryzen keeps the existing machine-specific CPU/kernel tuning described
in the main README. Review kernel, NVIDIA and boot choices for each device.
