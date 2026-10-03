#!/usr/bin/env python3
"""Build the portable Linux amd64 TUI bundle and retain dependency licences."""
import gzip
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'lib'))
from launcher import digest, source_hash


def json_stream(text):
    decoder = json.JSONDecoder()
    while text.strip():
        item, end = decoder.raw_decode(text.lstrip())
        yield item
        text = text.lstrip()[end:]


def build():
    version = (REPO / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must contain a numeric release version.')
    env = dict(os.environ, CGO_ENABLED='0', GOOS='linux', GOARCH='amd64', GOAMD64='v1',
               GOEXPERIMENT='', GOFLAGS='-mod=readonly', GOTOOLCHAIN='local')
    output = REPO / 'assets/bin'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='fiw-dots-release-') as temp:
        executable = Path(temp) / 'fiw-dots'
        subprocess.run(['go', 'build', '-trimpath', '-buildvcs=false',
                        '-ldflags=-s -w -X main.tuiVersion=' + version,
                        '-o', str(executable), './cmd/dots'], cwd=REPO, env=env, check=True)
        data = executable.read_bytes()
    archive = gzip.compress(data, mtime=0)
    name = 'fiw-dots-linux-amd64.gz'
    metadata = {'version': version, 'source_sha256': source_hash(),
                'binaries': {'linux-amd64': {'file': name, 'sha256': digest(data),
                    'gzip_sha256': digest(archive), 'size': len(data)}}}
    packages = subprocess.run(['go', 'list', '-deps', '-json', './cmd/dots'], cwd=REPO, env=env,
                             text=True, capture_output=True, check=True)
    modules = {package['Module']['Path']: package['Module'] for package in json_stream(packages.stdout)
               if package.get('Module') and not package['Module'].get('Main')}
    notices = ['# Third-party licences for the bundled TUI\n']
    for _, module in sorted(modules.items()):
        directory = Path(module['Dir'])
        licences = sorted(path for path in directory.iterdir() if path.is_file()
                          and path.name.lower().startswith(('license', 'copying', 'notice')))
        if not licences:
            raise RuntimeError('Missing licence notice for ' + module['Path'])
        for path in licences:
            notices += ['\n## ' + module['Path'] + ' ' + module['Version'] + ' / ' + path.name + '\n', path.read_text()]
    goroot = subprocess.run(['go', 'env', 'GOROOT'], env=env, text=True, capture_output=True, check=True).stdout.strip()
    license_path = Path(goroot) / 'LICENSE'
    if license_path.is_file():
        go_license = license_path.read_text()
    else:
        # Gentoo omits the upstream licence file from GOROOT. Obtain that
        # exact toolchain's notice from the official Go source repository.
        goversion = subprocess.run(['go', 'env', 'GOVERSION'], env=env, text=True, capture_output=True, check=True).stdout.strip()
        match = re.match(r'go\d+\.\d+(?:\.\d+)?', goversion)
        if not match:
            raise RuntimeError('Cannot identify the Go toolchain licence source.')
        url = 'https://raw.githubusercontent.com/golang/go/' + match.group() + '/LICENSE'
        with urllib.request.urlopen(url, timeout=20) as response:
            go_license = response.read().decode()
    notices += ['\n## Go standard library and runtime\n', go_license]
    (output / name).write_bytes(archive)
    (output / 'tui.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (output / 'SHA256SUMS').write_text(digest(archive) + '  ' + name + '\n')
    (output / 'LICENSES.txt').write_text('\n'.join(notices))
    print('Built v' + version + ': ' + str(len(data)) + ' bytes; compressed ' + str(len(archive)) + ' bytes.')
    print('Source and binary fingerprints: assets/bin/tui.json')


if __name__ == '__main__':
    build()
