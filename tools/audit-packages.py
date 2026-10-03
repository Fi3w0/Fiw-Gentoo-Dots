#!/usr/bin/env python3
"""Compare explicit world/set selections with main and optional package lists."""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def lines(path):
    if not path.is_file():
        return []
    return [line.split('#', 1)[0].strip() for line in path.read_text().splitlines()
            if line.split('#', 1)[0].strip()]


def package(atom):
    value = atom.split('::', 1)[0].split('[', 1)[0].lstrip('<>=~')
    base, _, slot = value.partition(':')
    base = re.sub(r'-[0-9].*$', '', base)
    if not re.fullmatch(r'[A-Za-z0-9+_.-]+/[A-Za-z0-9+_.-]+', base):
        raise ValueError('Invalid explicit package atom.')
    return base + (':' + slot if slot else '')


def explicit(world, world_sets, sets):
    selections, unresolved = {}, set()
    def read(items, origin, stack=()):
        for atom in items:
            if atom.startswith('@'):
                name = atom[1:]
                if not re.fullmatch(r'[A-Za-z0-9+_.-]+', name):
                    raise ValueError('Invalid selected set name.')
                if name in stack:
                    raise ValueError('Cyclic selected set: ' + name)
                source = sets / name
                if not source.is_file():
                    unresolved.add(name)
                else:
                    read(lines(source), '@' + name, stack + (name,))
            else:
                selections.setdefault(package(atom), set()).add(origin)
    read(lines(world), 'world')
    read(lines(world_sets), 'world_sets')
    return {atom: sorted(origins) for atom, origins in sorted(selections.items())}, sorted(unresolved)


def audit(world, world_sets, sets, repo=REPO):
    selected, unresolved = explicit(world, world_sets, sets)
    coverage = {}
    for path in sorted((repo / 'packages').rglob('*.list')):
        if path.name == 'source.list':
            continue
        category = path.relative_to(repo / 'packages').with_suffix('').as_posix()
        for atom in lines(path):
            coverage.setdefault(package(atom), set()).add(category)
    for atom, category in [('sys-kernel/gentoo-kernel', 'kernel/custom'),
                           ('sys-kernel/gentoo-kernel-bin', 'kernel/binary')]:
        coverage.setdefault(atom, set()).add(category)
    exceptions = json.loads((repo / 'packages/audit-exceptions.json').read_text())
    matched = {atom: sorted(coverage[atom]) for atom in selected if atom in coverage}
    manual = {atom: exceptions[atom] for atom in selected if atom in exceptions and atom not in coverage}
    missing = sorted(set(selected) - set(matched) - set(manual))
    return {'explicit_count': len(selected), 'covered_count': len(matched),
            'coverage': matched, 'sources': selected, 'manual_helpers': manual,
            'missing': missing, 'unresolved_sets': unresolved}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', type=Path, default=Path('/var/lib/portage/world'))
    parser.add_argument('--world-sets', type=Path, default=Path('/var/lib/portage/world_sets'))
    parser.add_argument('--sets', type=Path, default=Path('/etc/portage/sets'))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if not args.world.is_file() and not args.world_sets.is_file():
        parser.error('No Portage explicit selection files found.')
    result = audit(args.world, args.world_sets, args.sets)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(str(result['covered_count']) + '/' + str(result['explicit_count']) + ' explicit selections covered by package lists/kernel choices.')
        for atom, reason in result['manual_helpers'].items():
            print('Manual helper: ' + atom + ' — ' + reason)
        print('Missing main packages: ' + (', '.join(result['missing']) or 'none'))
        print('Unresolved selected sets: ' + (', '.join(result['unresolved_sets']) or 'none'))
    return 1 if result['missing'] or result['unresolved_sets'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
