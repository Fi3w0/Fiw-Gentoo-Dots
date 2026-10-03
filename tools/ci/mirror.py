#!/usr/bin/env python3
"""Publish Forgejo branches/tags to GitHub without deleting or forcing refs."""
import argparse
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
SOURCE = 'https://git.fiwlabs.dev/fiwdev/Fiw-Gentoo-Dots.git'
GITHUB_HOST = 'github.com'
GITHUB_REPOSITORY = 'Fi3w0/Fiw-Gentoo-Dots'
TARGET = f'ssh://git@{GITHUB_HOST}/{GITHUB_REPOSITORY}.git'


def mirror(source=SOURCE, target=TARGET, key=None, source_ref=None, source_sha=None):
    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    environment.pop('GH_MIRROR_SSH_KEY', None)
    with tempfile.TemporaryDirectory(prefix='fiw-github-mirror-') as temporary:
        root = Path(temporary)
        remote = urlsplit(target)
        if remote.scheme == 'ssh' and remote.hostname == GITHUB_HOST:
            if not key or not key.strip():
                raise RuntimeError('Add the GH_MIRROR_SSH_KEY repository secret in Forgejo before mirroring.')
            identity = root / 'identity'
            identity.write_text(key.strip() + '\n')
            identity.chmod(0o600)
            environment['GIT_SSH_COMMAND'] = shlex.join([
                'ssh', '-F', '/dev/null', '-i', str(identity),
                '-o', 'BatchMode=yes', '-o', 'IdentitiesOnly=yes',
                '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(REPO / 'tools/ci/github_known_hosts')])
        snapshot = root / 'source.git'
        subprocess.run(['git', 'clone', '--bare', '--no-local', source, str(snapshot)], env=environment, check=True)
        if source_ref:
            if not source_ref.startswith(('refs/heads/', 'refs/tags/')):
                raise RuntimeError('Mirror source must be a branch or tag ref.')
            subprocess.run(['git', 'check-ref-format', source_ref], env=environment, check=True)
            actual = subprocess.run(['git', '-C', str(snapshot), 'rev-parse', '--verify', source_ref + '^{commit}'], env=environment, text=True, capture_output=True)
            reviewed = subprocess.run(['git', '-C', str(snapshot), 'rev-parse', '--verify', (source_sha or '') + '^{commit}'], env=environment, text=True, capture_output=True)
            if actual.returncode or reviewed.returncode or actual.stdout != reviewed.stdout:
                print('Source ref changed or was removed since this CI run; a newer run can publish it.')
                return
        subprocess.run(['git', '-C', str(snapshot), 'push', '--atomic', target,
                        'refs/heads/*:refs/heads/*', 'refs/tags/*:refs/tags/*'], env=environment, check=True)
        print('Forgejo branches and tags published to GitHub.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=SOURCE)
    parser.add_argument('--target', default=TARGET)
    parser.add_argument('--key-file', type=Path, help='Local deploy key for an explicit manual sync')
    args = parser.parse_args()
    key = args.key_file.read_text() if args.key_file else os.environ.get('GH_MIRROR_SSH_KEY')
    mirror(args.source, args.target, key, os.environ.get('MIRROR_SOURCE_REF'), os.environ.get('MIRROR_SOURCE_SHA'))


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
