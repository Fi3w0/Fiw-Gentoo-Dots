"""Preview and restore user config backups, preserving the current files."""
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


def stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')


def user_state(home):
    home = home.resolve()
    state = home / '.local/state/Fiw-Gentoo-Dots'
    if not state.resolve().is_relative_to(home):
        raise RuntimeError('Config state directory points outside the target home.')
    backup_root = state / 'backups'
    if backup_root.is_symlink() or not backup_root.resolve().is_relative_to(state.resolve()):
        raise RuntimeError('Config backup directory points outside its managed location.')
    return state


def digest(path):
    if path.is_symlink():
        return 'link:' + os.readlink(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def files(home, backup_id, allowed):
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}(?:\.[0-9]+)?Z', backup_id):
        raise ValueError('Invalid config backup ID.')
    root = user_state(home) / 'backups' / backup_id
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError('Config backup not found: ' + backup_id)
    if not root.resolve().is_relative_to(user_state(home).resolve()):
        raise RuntimeError('Backup directory points outside config state.')
    result = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        if any((Path(directory) / name).is_symlink() for name in dirs):
            raise RuntimeError('A backup directory is a symlink; preserving all files.')
        for name in sorted(names):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if relative not in allowed:
                raise RuntimeError('Unrecognized file in config backup: ' + relative)
            if not path.is_file() and not path.is_symlink():
                raise RuntimeError('Unsupported config backup file: ' + relative)
            destination = home / relative
            if not destination.parent.resolve().is_relative_to(home.resolve()):
                raise RuntimeError('Config parent points outside the target home: ' + relative)
            if destination.is_dir() and not destination.is_symlink():
                raise RuntimeError('Config destination is a directory: ' + relative)
            result.append((relative, path, destination))
    return sorted(result)


def list_backups(home, allowed):
    root = user_state(home) / 'backups'
    if not root.exists():
        return []
    if root.is_symlink():
        raise RuntimeError('Config backup directory is a symlink.')
    choices = []
    for directory in sorted(root.iterdir(), reverse=True):
        if directory.is_dir() and re.fullmatch(r'[0-9]{8}T[0-9]{6}(?:\.[0-9]+)?Z', directory.name):
            entries = files(home, directory.name, allowed)
            if entries:
                choices.append({'id': directory.name, 'count': len(entries)})
    return choices


def plan(home, backup_id, allowed):
    entries = files(home, backup_id, allowed)
    return {'backup': backup_id, 'files': [
        {'path': relative, 'config': allowed[relative]['name'],
         'change': 'unchanged' if digest(source) == digest(destination) else 'restore'}
        for relative, source, destination in entries],
        'note': 'Current files get a new backup. Files created by the original restore are retained. Only user configs are restored.'}


def restore(home, backup_id, allowed, ask, active_plasma, conflict='ask'):
    if os.geteuid() == 0:
        raise RuntimeError('Restore user config backups as the target user, not root.')
    home = home.resolve()
    entries = files(home, backup_id, allowed)
    if any(allowed[relative].get('kde') for relative, _, _ in entries) and active_plasma(home):
        raise RuntimeError('Log out of Plasma before restoring a KDE config backup.')
    print(json.dumps(plan(home, backup_id, allowed), indent=2))
    report = {'backup': backup_id, 'restored': [], 'unchanged': [], 'kept': []}
    if not entries or ask('Restore the previewed user config backup?', ['restore', 'cancel'], 'cancel') != 'restore':
        report['status'] = 'cancelled'
        return report
    state = user_state(home)
    index_path = state / 'managed.json'
    index = json.loads(index_path.read_text()) if index_path.is_file() else {}
    backup_id_new = stamp()
    for relative, source, destination in entries:
        if digest(source) == digest(destination):
            report['unchanged'].append(relative)
            continue
        if destination.exists() or destination.is_symlink():
            if conflict == 'keep' or (conflict == 'ask' and ask('Restore ' + relative + ' after backing up the current file?', ['restore', 'keep'], 'keep') == 'keep'):
                report['kept'].append(relative)
                continue
            current = state / 'backups' / backup_id_new / relative
            current.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, current, follow_symlinks=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name('.' + destination.name + '.fiw-restore-' + backup_id_new)
        shutil.copy2(source, temporary, follow_symlinks=False)
        os.replace(temporary, destination)
        # A restored previous preference is a local choice; future updates
        # should propose changes rather than treating it as the current preset.
        index.pop(relative, None)
        report['restored'].append(relative)
    temporary = index_path.with_name('.managed-restore-' + backup_id_new)
    temporary.write_text(json.dumps(index, indent=2) + '\n')
    temporary.replace(index_path)
    report['current_backup'] = backup_id_new if (state / 'backups' / backup_id_new).exists() else None
    return report
