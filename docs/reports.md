# Restoration reports

Every TUI apply action ends with one combined report, including failure and
cancellation paths. It correlates the user's and root's steps by a generated
run ID and the saved selection. Reports from other runs are kept separate.

The report includes:

- Completed, partial, failed, cancelled and not attempted steps.
- Confirmed present Portage packages and skipped or missing packages.
- NVIDIA module checks/builds for a selected custom kernel and binary fallback.
- Installed, existing, skipped or failed user Flatpaks.
- Enabled, missing or skipped service units.
- Applied configs, preserved conflicts and pending `.new` proposals.
- Boot deployment, backup restoration or config proposal acceptance outcome.
- Missing config requirements and selected manual setup steps.

A cancelled operation stops the full restore sequence. Completed earlier
steps remain recorded; it does not undo their changes.

Combined reports live in `~/.local/state/Fiw-Gentoo-Dots/summary-RUN_ID.json`.
Each step also keeps its own local report. Existing detailed package and boot
reports remain in `/var/lib/Fiw-Gentoo-Dots`.

Show a summary for the latest run matching a saved selection:

```sh
./install --selection local/selection.json --summary
```

For a command-line sequence, use the same explicit run ID for all steps:

```sh
sudo ./install --selection local/selection.json --run-id my-restore --install-packages
./install --selection local/selection.json --run-id my-restore --install-flatpaks
./install --selection local/selection.json --run-id my-restore --apply-configs
./install --selection local/selection.json --run-id my-restore --summary
```

Run the combined summary as your regular user. `--workflow configs`,
`packages`, `flatpaks`, `services`, `boot`, `backup` or `proposal` limits the expected steps
when summarizing one action. Full restoration is the default. Without an
explicit ID, separate CLI apply commands are separate runs.
