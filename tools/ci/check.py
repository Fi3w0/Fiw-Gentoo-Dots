#!/usr/bin/env python3
"""Check portable code and the shipped assets without applying the installer."""
import gzip
import hashlib
import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_assets():
    spec = importlib.util.spec_from_file_location('launcher', REPO / 'lib/launcher.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    root = REPO / 'assets/bin'
    metadata = json.loads((root / 'tui.json').read_text())
    if metadata['version'] != (REPO / 'VERSION').read_text().strip():
        raise RuntimeError('TUI version does not match VERSION; rebuild the release bundle.')
    if metadata['source_sha256'] != launcher.source_hash(REPO):
        raise RuntimeError('TUI source changed; rebuild the release bundle.')
    for binary in metadata['binaries'].values():
        path = root / binary['file']
        if path.parent.resolve() != root.resolve():
            raise RuntimeError('Invalid TUI archive path.')
        compressed = path.read_bytes()
        if sha(compressed) != binary['gzip_sha256']:
            raise RuntimeError('TUI archive checksum mismatch.')
        size = binary['size']
        if not isinstance(size, int) or not 0 < size <= 64 * 1024 * 1024:
            raise RuntimeError('Invalid TUI size.')
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            executable = stream.read(size + 1)
        if len(executable) != size or sha(executable) != binary['sha256']:
            raise RuntimeError('TUI executable checksum mismatch.')
        line = binary['gzip_sha256'] + '  ' + binary['file']
        if line not in (root / 'SHA256SUMS').read_text().splitlines():
            raise RuntimeError('SHA256SUMS does not match the TUI archive.')
    for name, entry in json.loads((REPO / 'assets/editor-themes.json').read_text()).items():
        directory = REPO / entry['root']
        if not directory.resolve().is_relative_to(REPO):
            raise RuntimeError('Invalid editor asset directory.')
        actual = {path.relative_to(directory).as_posix(): sha(path.read_bytes())
                  for path in sorted(directory.rglob('*')) if path.is_file()}
        if actual != entry['sha256']:
            raise RuntimeError('Editor asset fingerprints changed: ' + name)
    print('Prebuilt TUI and editor asset fingerprints match.', flush=True)


def main():
    subprocess.run(['python3', 'tools/check-private.py'], cwd=REPO, check=True)
    check_assets()
    for directory in ('lib', 'tools'):
        for path in (REPO / directory).rglob('*.py'):
            compile(path.read_bytes(), path.relative_to(REPO).as_posix(), 'exec')
    print('Python sources parse.', flush=True)
    subprocess.run(['go', 'build', '-buildvcs=false', '-o', os.devnull, './cmd/dots'], cwd=REPO, check=True)
    print('Portable CI checks passed; no installer actions were applied.', flush=True)


if __name__ == '__main__':
    main()
