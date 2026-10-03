#!/usr/bin/env python3
"""Generate a readable reference from the captured KDE global shortcuts."""
from collections import defaultdict
from pathlib import Path

from capture import sections

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / 'configs/kde-shortcuts/kconfig/.config/kglobalshortcutsrc'


def bindings(value):
    return [key.strip() for key in value.replace(r'\t', '\t').split('\t')
            if key.strip() and key.strip().lower() != 'none']


def records(path=SOURCE):
    for group, values in sections(path.read_text()).items():
        for action, value in values.items():
            if action.startswith('_') and action != '_launch':
                continue
            fields = value.split(',', 2)
            current = bindings(fields[0])
            default = bindings(fields[1]) if len(fields) > 1 else None
            label = fields[2] if len(fields) > 2 else action
            yield group, action, label, current, default


def cell(value):
    return value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('|', '&#124;').replace('`', '&#96;')


def keys(values):
    if values is None:
        return '—'
    return '<br>'.join('<code>' + cell(value) + '</code>' for value in values) or 'Unassigned'


def generate():
    entries = list(records())
    active = [r for r in entries if r[3]]
    inactive = [r for r in entries if not r[3]]
    by_key = defaultdict(list)
    for group, action, label, current, default in active:
        for key in current:
            by_key[key].append(group + ' / ' + action)
    duplicates = {key: owners for key, owners in by_key.items() if len(owners) > 1}
    lines = ['# KDE shortcuts', '',
             'Generated from the repo’s captured `kglobalshortcutsrc`. This describes',
             'Fiw’s bindings as configured; applying them is a separate installer action.',
             'It covers KDE global shortcuts, not every shortcut inside individual applications.', '',
             f'**{len(active)} assigned actions · {len(inactive)} unassigned actions · {len(entries)} total**', '',
             '`Meta` is the Super/Windows key. In the full tables, multiple keys for',
             'one action are alternatives. Grouped summary keys match the named actions',
             'in order. “Unassigned” means explicitly disabled in this capture;',
             'a key in the KDE default column is not an active binding. The default',
             'column is copied from KDE’s stored values, not inferred from a release.', '',
             '## Everyday bindings', '',
             '| Keys | Action |', '|---|---|',
             'Screenshot bindings use `fiw-shot`: copy to clipboard, then offer Save',
             'or Edit in the notification. They need Spectacle, `wl-copy` and',
             '`notify-send`; Kitty and KRunner bindings need their respective apps.',
             'The native Spectacle bindings are unassigned to avoid competing actions.', '',
             'The desktop-move bindings are stored as literal symbols (`!`, `@`, `#`).',
             'On a US layout these usually mean Shift+1/2/3; other layouts can differ.',
             'The keyboard-layout preset contains US English, Russian and Spanish;',
             '`Meta+Alt+Space` cycles through them. The shortcut preset also restores',
             'the captured virtual-desktop count and rows. Device IDs are not copied;',
             'KWin creates IDs when needed and retains existing target IDs.', '',
             '## Captured choices', '']
    lookup = {(r[0], r[1]): r for r in entries}
    highlights = [
        ('Open application launcher', '[plasmashell]', ['activate application launcher']),
        ('Open KRunner', '[services][org.kde.krunner.desktop]', ['_launch']),
        ('Open Kitty', '[services][net.local.kitty.desktop]', ['_launch']),
        ('Select a screenshot region', '[services][net.local.fiw-shot-region.desktop]', ['_launch']),
        ('Screenshot monitor under pointer', '[services][net.local.fiw-shot-screen.desktop]', ['_launch']),
        ('Show clipboard history at pointer', '[plasmashell]', ['show-on-mouse-pos']),
        ('Switch to desktop 1 / 2 / 3', '[kwin]', ['Switch to Desktop 1', 'Switch to Desktop 2', 'Switch to Desktop 3']),
        ('Move window to desktop 1 / 2 / 3', '[kwin]', ['Window to Desktop 1', 'Window to Desktop 2', 'Window to Desktop 3']),
        ('Switch desktop left / right / up / down', '[kwin]', ['Switch One Desktop to the Left', 'Switch One Desktop to the Right', 'Switch One Desktop Up', 'Switch One Desktop Down']),
        ('Tile window left / right / up / down', '[kwin]', ['Window Quick Tile Left', 'Window Quick Tile Right', 'Window Quick Tile Top', 'Window Quick Tile Bottom']),
        ('Move window to previous / next screen', '[kwin]', ['Window to Previous Screen', 'Window to Next Screen']),
        ('Maximize window', '[kwin]', ['Window Maximize']),
        ('Toggle Overview', '[kwin]', ['Overview']),
        ('Toggle desktop grid', '[kwin]', ['Grid View']),
        ('Next / previous activity', '[plasmashell]', ['next activity', 'previous activity']),
        ('Lock session', '[ksmserver]', ['Lock Session']),
        ('Show logout screen', '[ksmserver]', ['Log Out']),
    ]
    at = lines.index('Screenshot bindings use `fiw-shot`: copy to clipboard, then offer Save')
    summary = []
    for label, group, actions in highlights:
        current = [key for action in actions for key in lookup.get((group, action), (None, None, None, [], None))[3]]
        summary.append('| ' + keys(current) + ' | ' + cell(label) + ' |')
    lines[at:at] = summary + ['']
    forward = lookup[('[kwin]', 'Walk Through Windows')][3]
    lines += [('Forward window switching is currently unassigned; reverse switching' if not forward else
               'Forward window switching uses ' + keys(forward) + '; reverse switching'),
              'uses `Alt+Shift+Tab` and `Meta+Shift+Tab`.', '',
              'Other currently unassigned shortcuts include Peek at Desktop (`Meta+D`',
              'in the default column), Minimize (`Meta+PgDown`), Restore',
              '(`Meta+Backspace`) and the window menu (`Alt+F3`). FiwNode’s four',
              'recorded global actions are unassigned. `Meta+1/2/3` are used for',
              'desktops, with the corresponding task-manager shortcuts disabled.', '']
    if duplicates:
        lines += ['Keys assigned to multiple captured actions:', '']
        for key, owners in duplicates.items():
            lines.append('- ' + keys([key]) + ': ' + cell('; '.join(owners)))
        lines.append('')
    desktop = sections((SOURCE.parent / 'kwinrc').read_text()).get('[Desktops]', {})
    lines += ['Captured desktop layout: **' + desktop.get('Number', 'unspecified') +
              ' desktop(s), ' + desktop.get('Rows', 'unspecified') + ' row(s)**.',
              'Bindings for desktops 1–3 are retained exactly as configured.', '']
    lines += ['## All assigned actions', '']
    grouped = defaultdict(list)
    for record in entries:
        grouped[record[0]].append(record)
    friendly = sections(SOURCE.read_text())
    launch_names = {'[services][net.local.fiw-shot-region.desktop]': 'Screenshot region helper',
                    '[services][net.local.fiw-shot-screen.desktop]': 'Screenshot monitor helper',
                    '[services][net.local.kitty.desktop]': 'Kitty launcher',
                    '[services][org.kde.krunner.desktop]': 'KRunner launcher'}
    for group, rows in grouped.items():
        assigned = [r for r in rows if r[3]]
        if not assigned:
            continue
        title = launch_names.get(group, friendly[group].get('_k_friendly_name', group.strip('[]')))
        lines += ['### ' + cell(title), '', '| Action | Current keys | Stored KDE default |', '|---|---|---|']
        for _, action, label, current, default in assigned:
            label = launch_names.get(group, label) if action == '_launch' else label
            lines.append('| ' + cell(label) + ' | ' + keys(current) + ' | ' + keys(default) + ' |')
        lines.append('')
    lines += ['## All unassigned actions', '',
              'These entries are restored as unassigned, including actions with a',
              'stored KDE default. Expand each section to review the full capture.', '']
    for group, rows in grouped.items():
        disabled = [r for r in rows if not r[3]]
        if not disabled:
            continue
        title = friendly[group].get('_k_friendly_name', group.strip('[]'))
        lines += ['<details>', '<summary>' + cell(title) + f' ({len(disabled)})</summary>', '',
                  '| Action | Stored KDE default |', '|---|---|']
        for _, action, label, current, default in disabled:
            lines.append('| ' + cell(label) + ' | ' + keys(default) + ' |')
        lines += ['', '</details>', '']
    lines += ['## Refresh the reference', '', '```sh', 'python3 tools/shortcuts.py', '```', '',
              'Run this after reviewing a shortcut capture or changing the preset.',
              'The generator reads repo files only and does not change live KDE settings.', '']
    dest = REPO / 'docs/shortcuts.md'
    dest.write_text('\n'.join(lines))
    print(f'Wrote docs/shortcuts.md: {len(active)} assigned, {len(inactive)} unassigned, {len(duplicates)} duplicate keys.')


if __name__ == '__main__':
    generate()
