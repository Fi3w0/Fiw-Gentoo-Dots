# Review config updates

After reviewing and pulling repository changes, launch `./install`. Your
saved selection is reused. At the final preview, press **e** to update the
selected configs. Locally edited files stay intact; the proposed content goes
to a separate `.new` file. Existing proposals are retained, with a timestamp
on subsequent proposals. Unchanged files are left alone. Other replacements
still have apply-or-keep prompts and backups.

Launch the TUI again and press **p** to browse pending proposals. Choose a
file to see its diff, then press Enter to begin the acceptance prompt.
Esc returns to the chooser. Acceptance defaults to keeping the current file.
You can accept each app's changes separately.

Pending files have these states:

| State | Meaning |
|---|---|
| `ready` | The current file matches the version used to generate the proposal. |
| `unchanged` | The current file already matches the proposal; acceptance clears that proposal. |
| `stale` | The current file changed after proposal creation. Update configs again to generate a fresh proposal. |

Acceptance rechecks the current file after confirmation. A newer edit stops
acceptance and preserves both files. A proposal edited during confirmation
also requires another review. Each replaced current file gets a backup
available through **u**. Only the accepted proposal is removed. If you edit a
proposal before accepting it, the resulting config is treated as a local
preference on future updates.

Close the affected app before accepting its config. KDE proposals require
logging out of Plasma and running from a TTY. Shared KDE files combine all
selected patches into one proposal, preserving unrelated keys.

The CLI equivalents are:

```sh
./install --selection local/selection.json --apply-configs --update
./install --list-proposals
./install --proposal-plan '.config/kitty/kitty.conf.new'
./install --accept-proposal '.config/kitty/kitty.conf.new'
```

Use the actual proposal ID shown by the list, including a timestamp if present.
Run these as the target user. The list includes proposals recorded by this
version of the installer. Older or manually created `.new` files remain on
disk; updating again creates a recorded proposal for review without replacing
those files. Proposal records live locally under
`~/.local/state/Fiw-Gentoo-Dots/proposals.json`.
