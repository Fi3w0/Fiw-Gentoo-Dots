#!/usr/bin/env python3
"""Run the matching bundled TUI, with a Go source fallback."""
import gzip
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def source_hash(repo=REPO):
    paths = [repo / name for name in ('go.mod', 'go.sum', 'VERSION')]
    for directory in ('cmd', 'internal'):
        paths += [path for path in (repo / directory).rglob('*.go') if not path.name.endswith('_test.go')]
    value = hashlib.sha256()
    for path in sorted(paths):
        value.update(path.relative_to(repo).as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
    return value.hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bundled(repo, cache):
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        raise RuntimeError('The bundled TUI supports Linux amd64.')
    root = repo / 'assets/bin'
    metadata = json.loads((root / 'tui.json').read_text())
    if metadata['source_sha256'] != source_hash(repo):
        raise RuntimeError('The bundled TUI does not match the frontend source in this checkout.')
    binary = metadata['binaries']['linux-amd64']
    path = root / binary['file']
    if path.parent.resolve() != root.resolve():
        raise RuntimeError('Invalid bundled TUI path.')
    if cache.is_file() and not cache.is_symlink() and digest(cache.read_bytes()) == binary['sha256']:
        cache.chmod(0o755)
        return cache
    compressed = path.read_bytes()
    if digest(compressed) != binary['gzip_sha256']:
        raise RuntimeError('Bundled TUI archive checksum mismatch.')
    size = binary['size']
    if not isinstance(size, int) or not 0 < size <= 64 * 1024 * 1024:
        raise RuntimeError('Invalid bundled TUI size.')
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        data = stream.read(size + 1)
    if len(data) != size or digest(data) != binary['sha256']:
        raise RuntimeError('Bundled TUI binary checksum mismatch.')
    cache.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=cache.parent, prefix='.fiw-dots-', delete=False) as file:
        temporary = Path(file.name)
        file.write(data)
    try:
        temporary.chmod(0o755)
        temporary.replace(cache)
    finally:
        temporary.unlink(missing_ok=True)
    return cache


def launch(repo=REPO):
    os.chdir(repo)
    cache = repo / 'build/fiw-dots'
    if os.environ.get('FIW_DOTS_SOURCE') != '1':
        try:
            return bundled(repo, cache)
        except (KeyError, ValueError, OSError, RuntimeError) as error:
            print('Prebuilt TUI unavailable: ' + str(error), file=sys.stderr)
    if not shutil.which('go'):
        raise RuntimeError('Use the v0.1.0 snapshot for its prebuilt Linux amd64 TUI, or install Go 1.24+ for source builds. Python CLI commands such as ./install --plan remain available.')
    print('Building the TUI from source with Go.', file=sys.stderr)
    cache.parent.mkdir(parents=True, exist_ok=True)
    version = (repo / 'VERSION').read_text().strip()
    env = dict(os.environ, CGO_ENABLED='0', GOTOOLCHAIN='local')
    subprocess.run(['go', 'build', '-trimpath', '-buildvcs=false', '-ldflags=-s -w -X main.tuiVersion=' + version,
                    '-o', str(cache), './cmd/dots'], env=env, check=True)
    return cache


if __name__ == '__main__':
    try:
        binary = launch()
        os.execv(binary, [str(binary)] + sys.argv[1:])
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print('TUI launcher: ' + str(error), file=sys.stderr)
        sys.exit(1)
