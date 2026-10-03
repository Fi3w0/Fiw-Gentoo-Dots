# Explicit package audit

The 2026-10-03 audit compares Portage `world` and the selected `@fiw-*` sets
with the main lists, optional lists and kernel choices. It reads explicit
selections only; it does not expand package dependencies or copy an installed
package inventory.

Result: **111 explicit selections accounted for**. 110 have package-list or
kernel coverage. `app-admin/fiw-scripts` supplies the two legacy helpers
already retained under `optional/`; that exception is documented in
`packages/audit-exceptions.json`. There are no unexplained missing packages
or unresolved sets.

The audit added `x11-misc/ydotool` to `cli`. It does not enable its daemon or
change input permissions. Filelight, Btrfs tools, NVIDIA drivers and TideWM
remain in their separate optional selections. Dolphin, Ark, Gwenview and
Spectacle remain in `fiw-apps`.

Repeat the audit on a device:

```sh
python3 tools/audit-packages.py
python3 tools/audit-packages.py --json > local/package-audit.json
```

Version pins and old repository qualifiers are normalized for coverage;
explicit Java slots remain distinct. Cyclic or missing selected sets are
reported rather than treated as covered. The tool does not change package
lists, Portage configuration or the device's world selections.
