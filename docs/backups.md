# Restore a config backup

At the final TUI preview, press **u** to browse user config backups. Choose a
backup to see its file list, then press Enter to begin the restore prompts.
Esc returns to the selection screen. An empty chooser does not apply anything.

The command-line equivalents are:

```sh
./install --list-backups
./install --backup-plan BACKUP_ID
./install --restore-backup BACKUP_ID
```

Run restoration as the target user. KDE backups require logging out of Plasma
and running from a TTY. The backup's contents determine this requirement,
independently of which presets are currently selected.

Restoration has a final confirmation and apply-or-keep prompts for existing
files. Each replaced current file gets a new backup. Afterwards, updates
treat the restored settings as local preferences and leave new proposals in
`.new` files. Unchanged files are left as they are.

Backups contain files replaced during earlier config application. Files first
created by that application are retained when restoring a backup. Unrelated
files are also retained. Only recognized config paths inside the target home
can be restored; unsafe directory links and unexpected backup paths stop the
operation before writes.

User backups live under `~/.local/state/Fiw-Gentoo-Dots/backups`. The TUI action
restores user configs. System Portage and boot backups remain available under
`/var/lib/Fiw-Gentoo-Dots/backups` for manual restoration.
