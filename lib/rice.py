#!/usr/bin/env python3
"""Selection, preview, config restoration and Portage installation backend."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from capture import sections

GROUPS = ['system', 'kde', 'fiw-apps', 'cli', 'dev', 'gaming', 'fiw-tools', 'tidewm']
EXTRAS = {'filelight': 'Filelight', 'btrfs': 'Btrfs tools', 'nvidia': 'NVIDIA drivers'}
CATALOG = json.loads((REPO / 'configs/catalog.json').read_text())
OWNERS = {'fish': 'fish', 'kitty': 'kitty', 'neovim': 'nvim', 'fastfetch': 'fastfetch',
          'vesktop': 'vesktop-bin', 'vscode': 'code', 'dolphin': 'dolphin', 'spectacle': 'spectacle'}
AUTOSTART_GROUPS = {'steam': 'gaming', 'spotify': 'fiw-apps', 'vesktop': 'fiw-apps',
                    'opendeck': 'fiw-tools', 'musicpresence': 'fiw-tools'}


def load_selection(path=None, profile='stock'):
    selection = json.loads((Path(path) if path else REPO / 'presets' / (profile + '.json')).read_text())
    if selection.get('profile') not in ('stock', 'fiw-ryzen'):
        raise ValueError('Unknown preset')
    for field, allowed in [('groups', GROUPS), ('configs', CATALOG), ('extras', EXTRAS)]:
        if any(x not in allowed for x in selection.get(field, [])):
            raise ValueError('Unknown selection in ' + field)
    if selection.get('kernel') not in ('binary', 'custom'):
        raise ValueError('Unknown kernel choice')
    if selection.get('bootloader') not in ('keep', 'limine', 'grub'):
        raise ValueError('Unknown bootloader choice')
    return selection


def atoms(path):
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')]


def package_map(selection):
    result = {group: atoms(REPO / 'packages' / (group + '.list')) for group in selection['groups']}
    if 'system' in result:
        result['system'] += ['sys-kernel/gentoo-kernel-bin']
        if selection['kernel'] == 'custom':
            snapshot = json.loads((REPO / 'optional/kernel/snapshot.json').read_text())
            result['system'] += [snapshot['atom']]
    for extra in selection.get('extras', []):
        result[extra] = atoms(REPO / 'packages/optional' / (extra + '.list'))
    if selection['bootloader'] != 'keep':
        result['boot-' + selection['bootloader']] = atoms(REPO / 'packages/optional' / (selection['bootloader'] + '.list'))
    return result


def source_policy(selection):
    result = atoms(REPO / 'packages/source.list')
    if selection['kernel'] == 'custom' and 'system' in selection['groups']:
        result += ['sys-kernel/gentoo-kernel']
        if 'nvidia' in selection.get('extras', []):
            result += ['x11-drivers/nvidia-drivers']
    return result


def merge_kconfig(old, patch):
    """Edit selected keys while retaining comments and unrelated groups/keys."""
    desired = sections(patch)
    old_groups = sections(old)
    if '[General]' in desired and 'rules' in desired['[General]']:
        rules = [r for r in old_groups.get('[General]', {}).get('rules', '').split(',') if r]
        rules += [r for r in desired['[General]']['rules'].split(',') if r]
        rules = list(dict.fromkeys(rules))
        desired['[General]']['rules'] = ','.join(rules)
        desired['[General]']['count'] = str(len(rules))
    lines, group, written, seen = [], None, set(), set()
    def missing():
        if group in desired:
            for key, value in desired[group].items():
                if (group, key) not in written:
                    lines.append(key + '=' + value)
                    written.add((group, key))
    for line in old.splitlines():
        if line.startswith('[') and line.endswith(']'):
            missing()
            group = line
            seen.add(group)
        elif group in desired and '=' in line and not line.startswith(('#', ';')):
            key = line.split('=', 1)[0]
            if key in desired[group]:
                if (group, key) in written:
                    continue
                line = key + '=' + desired[group][key]
                written.add((group, key))
        lines.append(line)
    missing()
    for group, values in desired.items():
        if group not in seen:
            lines += ['', group] + [k + '=' + v for k, v in values.items()]
    return '\n'.join(lines).strip('\n') + '\n'


def merge_json(old, patch):
    existing = json.loads(old) if old.strip() else {}
    def merge(a, b):
        for key, value in b.items():
            if isinstance(value, dict) and isinstance(a.get(key), dict):
                merge(a[key], value)
            else:
                a[key] = value
    merge(existing, json.loads(patch))
    return json.dumps(existing, indent=2) + '\n'


def config_entries(selection):
    for name in selection['configs']:
        for kind in ('files', 'kconfig', 'json'):
            root = REPO / 'configs' / name / kind
            if not root.is_dir():
                continue
            for src in sorted(root.rglob('*')):
                if not src.is_file() and not src.is_symlink():
                    continue
                relative = src.relative_to(root)
                if name == 'autostart' and relative.suffix == '.desktop':
                    if AUTOSTART_GROUPS.get(relative.stem) not in selection['groups']:
                        continue
                yield name, kind, src, relative


def digest(path):
    if path.is_symlink():
        return 'link:' + os.readlink(path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def ask(prompt, choices, default):
    if not sys.stdin.isatty():
        raise RuntimeError('Interactive confirmation required: ' + prompt)
    while True:
        reply = input(prompt + ' [' + '/'.join(choices) + '] (default ' + default + '): ').strip().lower() or default
        if reply in choices:
            return reply


def active_plasma(home):
    if home.resolve() != Path.home().resolve():
        return False
    result = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'plasmashell'], stdout=subprocess.DEVNULL)
    return result.returncode == 0


def apply_configs(selection, home, update=False, conflict='ask'):
    home = home.resolve()
    entries = list(config_entries(selection))
    if any(CATALOG[name].get('kde') for name, _, _, _ in entries) and active_plasma(home):
        raise RuntimeError('Log out of Plasma and apply from a TTY to prevent KDE overwriting restored settings. Portable app configs can be applied separately.')
    state_dir = home / '.local/state/Fiw-Gentoo-Dots'
    index_path = state_dir / 'managed.json'
    index = json.loads(index_path.read_text()) if index_path.is_file() else {}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    report = {'applied': [], 'unchanged': [], 'kept': [], 'review': [], 'missing': []}
    for name, kind, src, relative in entries:
        dest = home / relative
        # Keep writes inside the requested home, including through parent symlinks.
        if not dest.parent.resolve().is_relative_to(home):
            raise RuntimeError('Config parent points outside the target home: ' + str(relative))
        if name == 'autostart' and relative.suffix == '.desktop':
            command = src.read_text().split('Exec=', 1)[1].splitlines()[0].split()[0]
            if not shutil.which(command) and home == Path.home().resolve():
                report['missing'].append('Autostart skipped; missing command: ' + command)
                continue
        old_hash = digest(dest)
        if src.is_symlink():
            content = None
            new_hash = 'link:' + os.readlink(src)
        else:
            content = src.read_bytes()
            if '{{HOME}}' in content.decode(errors='ignore'):
                content = content.decode().replace('{{HOME}}', str(home)).encode()
            if kind in ('kconfig', 'json'):
                old_text = dest.read_text() if dest.is_file() else ''
                content = (merge_kconfig if kind == 'kconfig' else merge_json)(old_text, content.decode()).encode()
            new_hash = hashlib.sha256(content).hexdigest()
        key = str(relative)
        if old_hash == new_hash:
            report['unchanged'].append(key)
            continue
        target = dest
        if old_hash is not None:
            edited = update and old_hash != index.get(key)
            if edited:
                target = Path(str(dest) + '.new')
                report['review'].append(str(target.relative_to(home)))
                # Never replace a previously edited .new file.
                if target.exists() or target.is_symlink():
                    target = Path(str(target) + '.' + stamp)
                    report['review'][-1] = str(target.relative_to(home))
            elif conflict == 'keep' or (conflict == 'ask' and ask('Replace ' + key + ' after backing it up?', ['apply', 'keep'], 'keep') == 'keep'):
                report['kept'].append(key)
                continue
            else:
                backup = state_dir / 'backups' / stamp / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest, backup, follow_symlinks=False)
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.parent / ('.' + target.name + '.fiw-dots-' + stamp)
        if src.is_symlink():
            os.symlink(os.readlink(src), tmp)
        else:
            tmp.write_bytes(content)
            tmp.chmod(src.stat().st_mode & 0o777)
        os.replace(tmp, target)
        if target == dest:
            index[key] = new_hash
            report['applied'].append(key)
    state_dir.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=2) + '\n')
    (state_dir / 'selection.json').write_text(json.dumps(selection, indent=2) + '\n')
    (state_dir / ('report-' + stamp + '.json')).write_text(json.dumps(report, indent=2) + '\n')
    if 'fonts' in selection['configs'] and home == Path.home().resolve() and shutil.which('fc-cache'):
        subprocess.run(['fc-cache', str(home / '.local/share/fonts/Fiw-Gentoo-Dots')], check=True)
    print(json.dumps({k: len(v) for k, v in report.items()}, indent=2))
    for key in ('review', 'missing'):
        for value in report[key]:
            print(key + ': ' + value)
    return report


def root_files(selection, repo_location=None):
    """Return the proposed root files without modifying the host."""
    result = {}
    layers = ['common'] + selection['groups'] + selection.get('extras', []) + [selection['profile']]
    for layer in layers:
        source = REPO / 'portage' / layer
        if not source.is_dir():
            continue
        for src in source.rglob('*'):
            if not src.is_file():
                continue
            relative = src.relative_to(source)
            if len(relative.parts) == 1:
                dest = Path('etc/portage') / relative
            elif relative.parts[0] == 'env':
                dest = Path('etc/portage') / relative
            else:
                dest = Path('etc/portage') / relative.parent / ('fiw-dots-' + layer + '-' + relative.name)
            result[str(dest)] = src.read_text()
    for group, packages in package_map(selection).items():
        result['etc/portage/sets/fiw-dots-' + group] = '\n'.join(packages) + '\n'
    result['etc/portage/sets/fiw-dots'] = '\n'.join('@fiw-dots-' + g for g in package_map(selection)) + '\n'
    result['etc/portage/fiw-dots.conf'] += '\n# Persist the selected binary/source policy for later emerge operations.\n'
    result['etc/portage/fiw-dots.conf'] += 'EMERGE_DEFAULT_OPTS="${EMERGE_DEFAULT_OPTS} --getbinpkg ' + ' '.join('--usepkg-exclude=' + atom for atom in source_policy(selection)) + '"\n'
    result['etc/portage/repos.conf/fiw-dots.conf'] = '[fiw-dots]\nlocation = ' + str(repo_location or REPO / 'overlay') + '\npriority = 40\nauto-sync = no\n'
    for name, uri in [('guru', 'https://github.com/gentoo-mirror/guru.git'), ('steam-overlay', 'https://github.com/anyc/steam-overlay.git')]:
        result['etc/portage/repos.conf/fiw-dots-' + name + '.conf'] = '[' + name + ']\nlocation = /var/db/repos/' + name + '\nsync-type = git\nsync-uri = ' + uri + '\nsync-depth = 1\npriority = 10\n'
    arch = 'x86-64-v3' if selection['profile'] == 'fiw-ryzen' else 'x86-64'
    result['etc/portage/binrepos.conf/fiw-dots.conf'] = '[gentoo]\npriority = 1\nsync-uri = https://distfiles.gentoo.org/releases/amd64/binpackages/23.0/' + arch + '/\nlocation = /var/cache/binhost/gentoo\nverify-signature = true\n'
    if selection['kernel'] == 'custom' and 'system' in selection['groups']:
        for src in (REPO / 'optional/kernel/config.d').glob('*.config'):
            result['etc/kernel/config.d/' + src.name] = src.read_text()
        result['etc/portage/package.accept_keywords/fiw-dots-kernel'] = 'sys-kernel/gentoo-kernel ~amd64\nsys-kernel/gentoo-kernel-bin ~amd64\nvirtual/dist-kernel ~amd64\n'
        result['etc/portage/env/sys-kernel/gentoo-kernel'] = (REPO / 'optional/kernel/guard').read_text()
        result['etc/portage/package.mask/fiw-dots-custom-kernel'] = '# Tested custom-kernel snapshot; update snapshot and patch explicitly.\n>sys-kernel/gentoo-kernel-7.2.8\n'
    if 'tidewm' in selection['groups']:
        result['etc/portage/package.accept_keywords/fiw-dots-tidewm'] = 'gui-wm/tidewm::fiw-dots **\n'
    return result


def preview(selection):
    packages = package_map(selection)
    lines = ["Fiw-Gentoo-Dots — " + selection['name'], '']
    for group, values in packages.items():
        lines += [group + ' (' + str(len(values)) + ')', '  ' + ', '.join(values)]
    lines += ['', 'Compile deliberately: ' + ', '.join(source_policy(selection)),
              'Other packages: prefer binaries; ask compile/skip for additional source builds.',
              'Kernel: ' + selection['kernel'] + (' + binary fallback' if selection['kernel'] == 'custom' else ''),
              'Bootloader: ' + selection['bootloader'], '', 'Selected configs:']
    for name in selection['configs']:
        lines.append('  ' + name + ': ' + CATALOG[name]['label'])
    lines += ['', 'Config files: ' + str(len(list(config_entries(selection)))),
              'Root configuration files: ' + str(len(root_files(selection))),
              'Existing config conflicts: ask; updates preserve edits as .new.']

    if selection['bootloader'] != 'keep':
        lines.append('Bootloader package selected; ESP/firmware deployment is a separate explicit setup step (docs/boot.md).')
    if selection.get('firefox_privacy'):
        lines.append('Optional manual setup: Firefox-Privacy (docs/firefox.md).')
    if selection.get('spotify_custom'):
        lines.append('Optional manual setup: Spotify customization (docs/spotify.md). Stock Spotify is installed first.')
    return '\n'.join(lines)


def export(selection, dest):
    dest.mkdir(parents=True, exist_ok=True)
    for relative, content in root_files(selection).items():
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    if selection['kernel'] == 'custom' and 'system' in selection['groups']:
        patches = dest / 'etc/portage/patches/sys-kernel/gentoo-kernel'
        patches.mkdir(parents=True, exist_ok=True)
        for src in (REPO / 'optional/kernel/patches').glob('*.patch'):
            shutil.copy2(src, patches / src.name)
    (dest / 'selection.json').write_text(json.dumps(selection, indent=2) + '\n')
    (dest / 'PLAN.txt').write_text(preview(selection) + '\n')
    print('Exported root configuration and plan to ' + str(dest))


def cp_from_cpv(cpv):
    return re.sub(r'-\d.*$', '', cpv)


def source_builds(output):
    values = set(re.findall(r'^\[ebuild[^\]]*\]\s+(?:\([^)]*\)\s+)?([^\s:]+)', output, re.M))
    # Dedicated -bin ebuilds install upstream binaries; these do not require
    # compiling the application just because Portage labels them "ebuild".
    # This released Plasma widget installs QML/scripts without a compile phase.
    no_compile = {'kde-misc/apdatifier-gentoo'}
    return {value for value in values if not cp_from_cpv(value).endswith('-bin')
            and cp_from_cpv(value) not in no_compile}


def resolve(stage, selection, packages, execute=False):
    exclusions = ' '.join(source_policy(selection))
    command = ['emerge', '--config-root=' + str(stage), '--color=n', '--getbinpkg', '--usepkg',
               '--usepkg-exclude=' + exclusions, '--autounmask=n', '--noreplace']
    if not execute:
        command += ['--pretend']
    env = dict(os.environ, EMERGE_DEFAULT_OPTS='')
    return subprocess.run(command + packages, env=env, text=True,
                          stdout=None if execute else subprocess.PIPE,
                          stderr=None if execute else subprocess.STDOUT)


def install_packages(selection):
    if os.geteuid() != 0:
        raise RuntimeError('Package installation requires root. Run sudo ./install --install-packages --selection <file>.')
    if selection['profile'] == 'fiw-ryzen':
        cpu = Path('/proc/cpuinfo').read_text()
        if 'AuthenticAMD' not in cpu or '9900X' not in cpu:
            raise RuntimeError("Fiw's Ryzen targets the Ryzen 9900X/Zen 5 setup. Choose Stock on other devices.")
    requested = list(dict.fromkeys(p for values in package_map(selection).values() for p in values))
    if not requested:
        raise RuntimeError('No packages selected')
    with tempfile.TemporaryDirectory(prefix='fiw-dots-portage-') as temp:
        stage = Path(temp)
        shutil.copytree('/etc/portage', stage / 'etc/portage', symlinks=True,
                        ignore=shutil.ignore_patterns('gnupg'))
        profile = stage / 'etc/portage/make.profile'
        profile.unlink()
        profile.symlink_to(Path('/etc/portage/make.profile').resolve())
        export(selection, stage)
        make_conf = stage / 'etc/portage/make.conf'
        make_conf.write_text(make_conf.read_text() + '\nsource "' + str(stage / 'etc/portage/fiw-dots.conf') + '"\n')
        # Repository checkout is local and read-only for resolution. No live
        # root files are changed before successful resolution and confirmation.
        accepted, skipped = list(requested), []
        approved = set(source_policy(selection))
        while accepted:
            plan = resolve(stage, selection, accepted)
            print(plan.stdout)
            if plan.returncode:
                raise RuntimeError('Portage could not resolve the selection. No live configuration was applied; sync repositories or correct the reported masks first.')
            unexpected = sorted({cp_from_cpv(x) for x in source_builds(plan.stdout)} - approved)
            if not unexpected:
                break
            declined = set()
            for package in unexpected:
                if ask('No suitable binary for ' + package + '. Compile recommended.', ['compile', 'skip'], 'compile') == 'compile':
                    approved.add(package)
                else:
                    declined.add(package)
            if declined:
                retained = []
                for package in accepted:
                    single = resolve(stage, selection, [package])
                    needed = {cp_from_cpv(x) for x in source_builds(single.stdout)}
                    if single.returncode or needed & declined:
                        skipped.append(package)
                    else:
                        retained.append(package)
                if retained == accepted:
                    raise RuntimeError('Cannot safely remove the skipped dependency from this selection.')
                accepted = retained
        print('Skipped: ' + (', '.join(skipped) or 'none'))
        if not accepted:
            print('All requested packages were skipped; no live configuration applied.')
            return
        if ask('Apply the previewed Portage files and install the accepted packages?', ['apply', 'cancel'], 'cancel') != 'apply':
            return
        # Back up each existing managed destination before replacing it.
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        backup_root = Path('/var/lib/Fiw-Gentoo-Dots/backups') / stamp
        for relative, content in root_files(selection, '/var/db/repos/fiw-dots').items():
            dest = Path('/') / relative
            if relative.startswith('etc/portage/sets/'):
                continue
            if dest.is_file() and dest.read_text() == content:
                continue
            if dest.exists() or dest.is_symlink():
                if ask('Replace managed system file ' + relative + ' with a backup?', ['apply', 'keep'], 'keep') == 'keep':
                    continue
                backup = backup_root / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dest, backup, follow_symlinks=False)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        if selection['kernel'] == 'custom' and 'system' in selection['groups']:
            patch_dir = Path('/etc/portage/patches/sys-kernel/gentoo-kernel')
            patch_dir.mkdir(parents=True, exist_ok=True)
            for src in (REPO / 'optional/kernel/patches').glob('*.patch'):
                dest = patch_dir / src.name
                if dest.exists():
                    backup = backup_root / dest.relative_to('/')
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest, backup)
                shutil.copy2(src, dest)
        overlay = Path('/var/db/repos/fiw-dots')
        if overlay.exists():
            shutil.copytree(overlay, backup_root / 'overlay', symlinks=True)
        shutil.copytree(REPO / 'overlay', overlay, dirs_exist_ok=True, symlinks=True)
        make_conf = Path('/etc/portage/make.conf')
        include = 'source /etc/portage/fiw-dots.conf'
        if include not in make_conf.read_text():
            backup = backup_root / 'etc/portage/make.conf'
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(make_conf, backup)
            with make_conf.open('a') as stream:
                stream.write('\n# Fiw-Gentoo-Dots selected preset\n' + include + '\n')
        selected = Path('/etc/portage/sets/fiw-dots-selected')
        selected.parent.mkdir(parents=True, exist_ok=True)
        selected.write_text('\n'.join(accepted) + '\n')
        Path('/var/tmp/notmpfs').mkdir(parents=True, exist_ok=True)
        # Resolve once more against the live configuration; abort if the source
        # build list changed between review and installation.
        final = resolve(Path('/'), selection, ['@fiw-dots-selected'])
        if final.returncode or ({cp_from_cpv(x) for x in source_builds(final.stdout)} - approved):
            raise RuntimeError('The final package plan changed. Review it before retrying; backups are at ' + str(backup_root))
        result = resolve(Path('/'), selection, ['@fiw-dots-selected'], execute=True)
        missing = [atom for atom in requested if subprocess.run(
            ['portageq', 'has_version', '/', atom], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL).returncode != 0]
        report = {'requested': requested, 'skipped': skipped, 'emerge_exit_code': result.returncode,
                  'missing': missing,
                  'pending': []}
        state = Path('/var/lib/Fiw-Gentoo-Dots')
        state.mkdir(parents=True, exist_ok=True)
        (state / ('packages-' + stamp + '.json')).write_text(json.dumps(report, indent=2) + '\n')
        print('Package report: ' + str(state / ('packages-' + stamp + '.json')))
        print('Missing packages: ' + (', '.join(missing) or 'none'))
        if result.returncode:
            raise RuntimeError('Some packages did not install; consult the package report and emerge output.')
        if 'kde' in selection['groups'] and 'kde-plasma/plasma-login-manager' not in missing:
            subprocess.run(['systemctl', 'enable', '--force', 'plasmalogin.service'], check=True)
        print('Portage installation finished. Plasma Login Manager is enabled for selected KDE installs; no running greeter was restarted. Flatpaks and boot deployment are explicit follow-up steps; see docs/setup.md.')


def check_packages(selection):
    """Resolve against a staged copy of the current Portage configuration."""
    requested = list(dict.fromkeys(p for values in package_map(selection).values() for p in values))
    with tempfile.TemporaryDirectory(prefix='fiw-dots-check-') as temp:
        stage = Path(temp)
        shutil.copytree('/etc/portage', stage / 'etc/portage', symlinks=True,
                        ignore=shutil.ignore_patterns('gnupg'))
        profile = stage / 'etc/portage/make.profile'
        profile.unlink()
        profile.symlink_to(Path('/etc/portage/make.profile').resolve())
        export(selection, stage)
        make_conf = stage / 'etc/portage/make.conf'
        make_conf.write_text(make_conf.read_text() + '\nsource "' + str(stage / 'etc/portage/fiw-dots.conf') + '"\n')
        result = resolve(stage, selection, requested)
        print(result.stdout)
        if result.returncode:
            raise RuntimeError('The staged package plan could not be resolved. No live files were changed.')
        extra = {cp_from_cpv(value) for value in source_builds(result.stdout)} - set(source_policy(selection))
        print('Additional source-build choices required: ' + (', '.join(sorted(extra)) or 'none'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection')
    parser.add_argument('--profile', choices=['stock', 'fiw-ryzen'], default='stock')
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--catalog', action='store_true')
    parser.add_argument('--export', type=Path)
    parser.add_argument('--apply-configs', action='store_true')
    parser.add_argument('--install-packages', action='store_true')
    parser.add_argument('--check-packages', action='store_true')
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--conflict', choices=['ask', 'keep', 'apply'], default='ask')
    args = parser.parse_args()
    if args.catalog:
        print(json.dumps({'groups': GROUPS, 'configs': CATALOG, 'extras': EXTRAS,
                          'stock': load_selection(profile='stock'), 'ryzen': load_selection(profile='fiw-ryzen')}))
        return
    selection = load_selection(args.selection, args.profile)
    if args.export:
        export(selection, args.export)
    elif args.apply_configs:
        if os.geteuid() == 0:
            raise RuntimeError('Apply user configs as the target user, not as root.')
        apply_configs(selection, args.home, args.update, args.conflict)
    elif args.install_packages:
        install_packages(selection)
    elif args.check_packages:
        check_packages(selection)
    else:
        print(preview(selection))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
