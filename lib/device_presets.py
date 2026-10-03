"""Named local selections for individual devices; no hardware identifiers."""
import json
import re
import tempfile
from pathlib import Path


def path(repo, name):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,47}', name):
        raise ValueError('Use 1–48 lowercase letters, digits, underscores or hyphens for a device preset name.')
    root = repo / 'local/devices'
    if not root.resolve().is_relative_to(repo.resolve()):
        raise RuntimeError('Device preset directory points outside the checkout.')
    target = root / (name + '.json')
    if target.is_symlink():
        raise RuntimeError('Device preset is a symlink; preserving it.')
    return target


def list_presets(repo, load):
    root = repo / 'local/devices'
    result = {}
    for candidate in sorted(root.glob('*.json')):
        try:
            checked = path(repo, candidate.stem)
            result[candidate.stem] = load(checked)
        except (ValueError, OSError, RuntimeError):
            # A malformed local file cannot block the normal installer.
            continue
    return result


def save(repo, name, selection, ask):
    destination = path(repo, name)
    if destination.exists() and ask('Replace saved device preset ' + name + '?', ['save', 'keep'], 'keep') != 'save':
        print('Kept device preset: ' + name)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Use a new inode and refuse links; saved selections stay user-readable only.
    with tempfile.NamedTemporaryFile(mode='w', dir=destination.parent, prefix='.device-', delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(dict(selection, name=name), stream, indent=2)
        stream.write('\n')
    try:
        temporary.chmod(0o600)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print('Saved device preset: ' + name)
