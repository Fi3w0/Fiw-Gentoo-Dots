#!/usr/bin/env python3
"""Check publishable files; print locations, never matching secret contents."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PATTERNS = {
    'personal home path': re.compile(r'/home/(?!<|\{|\$)[A-Za-z0-9_.-]+'),
    'machine UUID': re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I),
    'LAN address': re.compile(r'\b(?:192\.168\.|10\.\d+\.|172\.(?:1[6-9]|2\d|3[01])\.)\d+\.\d+\b'),
    'MAC address': re.compile(r'\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b', re.I),
    'access token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{30,})\b'),
    'email address': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    'literal secret': re.compile(r'(?im)^\s*[\w.-]*(?:password|api[_-]?key|auth[_-]?token)[\w.-]*\s*[=:]\s*["\'][^"\'\n$]{12,}["\']'),
}


def check():
    result = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=REPO, text=True, capture_output=True)
    if result.returncode:
        files = [p.relative_to(REPO).as_posix() for p in REPO.rglob('*') if p.is_file()
                 and not any(part in ('local', 'build', '.git', '__pycache__') for part in p.relative_to(REPO).parts)]
    else:
        files = result.stdout.splitlines()
    snapshot = json.loads((REPO / 'optional/kernel/snapshot.json').read_text())
    attribution = json.loads((REPO / 'tools/public-attribution.json').read_text())
    errors = []
    for relative in sorted(set(files)):
        path = REPO / relative
        if path.is_symlink():
            if path.readlink().is_absolute():
                errors.append(relative + ': absolute symlink')
            continue
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if relative.startswith('optional/kernel/patches/'):
            if hashlib.sha256(raw).hexdigest() != snapshot['patch_sha256']:
                errors.append(relative + ': upstream patch checksum changed')
            # Reviewed upstream source patch contains public test UUIDs and
            # author addresses; only this fingerprinted artifact is exempt.
            continue
        if b'\0' in raw:
            continue
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            continue
        # Third-party licence notices must remain intact.
        if path.name.lower().startswith(('license', 'copying')):
            continue
        for reason, pattern in PATTERNS.items():
            if reason == 'email address' and attribution.get(relative) == hashlib.sha256(raw).hexdigest():
                # Original upstream author/contact credits, not user account data.
                # Only the reviewed exact files receive this email-only exception.
                continue
            for match in pattern.finditer(text):
                errors.append(relative + ':' + str(text.count('\n', 0, match.start()) + 1) + ': ' + reason)
    if errors:
        print('\n'.join(errors))
        return 1
    print('Private-data checks passed (' + str(len(set(files))) + ' files).')
    return 0


if __name__ == '__main__':
    raise SystemExit(check())
