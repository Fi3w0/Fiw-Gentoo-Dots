"""Review config update proposals and accept them without losing newer edits."""
import difflib
import json
import os
import re
import shutil
from pathlib import Path

from backups import digest, stamp, user_state


def registry(home):
    path = user_state(home) / 'proposals.json'
    return json.loads(path.read_text()) if path.is_file() else {}


def save(home, entries):
    path = user_state(home) / 'proposals.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.proposals-' + stamp())
    temporary.write_text(json.dumps(entries, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)


def record(home, proposal, target, base_hash, configs):
    entries = registry(home)
    entries[str(proposal)] = {'target': str(target), 'base_sha256': base_hash,
                              'proposed_sha256': digest(home / proposal),
                              'configs': configs, 'created': stamp()}
    save(home, entries)


def inspect(home, proposal_id, allowed):
    home = home.resolve()
    entry = registry(home).get(proposal_id)
    if not entry or entry.get('target') not in allowed:
        raise RuntimeError('Unrecognized config proposal.')
    target = entry['target']
    if not re.fullmatch(re.escape(target) + r'\.new(?:\.[0-9]{8}T[0-9]{6}\.[0-9]+Z)?', proposal_id):
        raise RuntimeError('Invalid config proposal path.')
    candidate, destination = home / proposal_id, home / target
    for path in (candidate, destination):
        if not path.parent.resolve().is_relative_to(home) or (path.is_dir() and not path.is_symlink()):
            raise RuntimeError('Unsafe config proposal or destination path.')
    if not candidate.is_file() and not candidate.is_symlink():
        raise FileNotFoundError('Config proposal no longer exists.')
    current = digest(destination)
    status = 'unchanged' if current == digest(candidate) else 'ready' if current == entry['base_sha256'] else 'stale'
    return entry, candidate, destination, status


def list_proposals(home, allowed):
    result = []
    for proposal_id in sorted(registry(home)):
        # Accepted or manually removed proposal files are not pending.
        try:
            entry, _, _, status = inspect(home, proposal_id, allowed)
        except FileNotFoundError:
            continue
        result.append({'id': proposal_id, 'target': entry['target'], 'status': status})
    return result


def preview(home, proposal_id, allowed):
    entry, candidate, destination, status = inspect(home, proposal_id, allowed)
    lines = ['Config update proposal: ' + proposal_id, 'Target: ' + entry['target'], 'Status: ' + status, '']
    if status == 'stale':
        lines += ['The target changed after this proposal was created.',
                  'Run a config update to generate a fresh proposal. This one will be kept.', '']
    if candidate.is_symlink() or destination.is_symlink():
        lines += ['Current: ' + str(digest(destination)), 'Proposed: ' + str(digest(candidate))]
    else:
        current = destination.read_bytes() if destination.is_file() else b''
        proposed = candidate.read_bytes()
        try:
            if b'\0' in current + proposed:
                raise UnicodeError
            diff = difflib.unified_diff(current.decode().splitlines(), proposed.decode().splitlines(),
                                        fromfile=entry['target'], tofile=proposal_id, lineterm='')
            lines += list(diff) or ['No content changes.']
        except UnicodeError:
            lines += ['Binary file: ' + str(len(current)) + ' -> ' + str(len(proposed)) + ' bytes.',
                      'Current SHA256: ' + str(digest(destination)), 'Proposed SHA256: ' + str(digest(candidate))]
    return '\n'.join(lines)


def accept(home, proposal_id, allowed, ask, active_plasma):
    if os.geteuid() == 0:
        raise RuntimeError('Accept user config proposals as the target user, not root.')
    home = home.resolve()
    entry, candidate, destination, status = inspect(home, proposal_id, allowed)
    if status == 'stale':
        raise RuntimeError('The target changed since this proposal was created. Update configs again; the old proposal is preserved.')
    if allowed[entry['target']].get('kde') and active_plasma(home) and status != 'unchanged':
        raise RuntimeError('Log out of Plasma before accepting a KDE config proposal.')
    proposed_hash = digest(candidate)
    print(preview(home, proposal_id, allowed))
    report = {'applied': [], 'unchanged': [], 'kept': []}
    if ask('Accept this previewed proposal and back up the current file?', ['apply', 'keep'], 'keep') != 'apply':
        report['kept'] = [proposal_id]
        return report
    # Check again after the confirmation in case the app rewrote its config.
    entry, candidate, destination, status = inspect(home, proposal_id, allowed)
    if status == 'stale':
        raise RuntimeError('The target changed during review. The proposal and current file are preserved.')
    if digest(candidate) != proposed_hash:
        raise RuntimeError('The proposal changed during review. Review it again; both files are preserved.')
    state = user_state(home)
    timestamp = stamp()
    if status != 'unchanged':
        backup = state / 'backups' / timestamp / entry['target']
        if destination.exists() or destination.is_symlink():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, backup, follow_symlinks=False)
        temporary = destination.with_name('.' + destination.name + '.fiw-proposal-' + timestamp)
        shutil.copy2(candidate, temporary, follow_symlinks=False)
        os.replace(temporary, destination)
        report['applied'] = [entry['target']]
    else:
        report['unchanged'] = [entry['target']]
    index_path = state / 'managed.json'
    index = json.loads(index_path.read_text()) if index_path.is_file() else {}
    if digest(destination) == entry.get('proposed_sha256'):
        index[entry['target']] = digest(destination)
    else:
        # A manually edited proposal is a local preference on future updates.
        index.pop(entry['target'], None)
    temporary = index_path.with_name('.managed-proposal-' + timestamp)
    temporary.write_text(json.dumps(index, indent=2) + '\n')
    temporary.replace(index_path)
    entries = registry(home)
    entries.pop(proposal_id, None)
    save(home, entries)
    candidate.unlink()
    report['backup'] = timestamp if (state / 'backups' / timestamp).exists() else None
    return report
