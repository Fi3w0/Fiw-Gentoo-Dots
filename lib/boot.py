#!/usr/bin/env python3
"""Preview and deploy a separate amd64 UEFI Limine or GRUB installation."""
import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('/etc/fiw-gentoo-dots/boot.json')
MANAGED = Path('/var/lib/Fiw-Gentoo-Dots')
BEGIN = '# >>> Fiw-Gentoo-Dots kernels'
END = '# <<< Fiw-Gentoo-Dots kernels'
EFI_DIRECTORY = 'EFI/Fiw-Gentoo'
GRUB_DIRECTORY = Path('/boot/fiw-gentoo')


def mount_info(path, exact=False):
    result = subprocess.run(['findmnt', '--json', '--mountpoint' if exact else '--target',
                             str(path), '--output', 'TARGET,SOURCE,FSTYPE,UUID,OPTIONS'],
                            text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('Not a mounted filesystem: ' + str(path))
    data = json.loads(result.stdout)['filesystems'][0]
    return data


def discover_esp(path=None):
    candidates = [Path(path)] if path else [Path('/efi'), Path('/boot/efi'), Path('/boot')]
    for candidate in candidates:
        try:
            info = mount_info(candidate, exact=True)
        except RuntimeError:
            continue
        if info['fstype'] not in ('vfat', 'fat', 'fat32'):
            continue
        source = re.sub(r'\[.*\]$', '', info['source'])
        device = Path(source).resolve()
        partition = Path('/sys/class/block') / device.name / 'partition'
        if not partition.is_file():
            continue
        # Require the GPT ESP type, not an arbitrary mounted FAT data partition.
        result = subprocess.run(['lsblk', '--noheadings', '--nodeps', '--output', 'PARTTYPE', str(device)],
                                text=True, capture_output=True)
        esp_type = 'c12a7328f81f11d2ba4b00a0c93ec93b'  # GPT ESP type, without separators
        if result.returncode or result.stdout.strip().lower().replace('-', '') != esp_type:
            continue
        parent = (Path('/sys/class/block') / device.name).resolve().parent.name
        identifier = subprocess.run(['lsblk', '--noheadings', '--nodeps', '--output', 'PARTUUID', str(device)], text=True, capture_output=True)
        return {'partuuid': identifier.stdout.strip().lower(), 'path': str(candidate.resolve()), 'device': str(device),
                'disk': '/dev/' + parent, 'partition': int(partition.read_text())}
    raise RuntimeError('Select a mounted GPT EFI System Partition with --esp. No ESP was found.')


def kernel_images(boot=Path('/boot'), exclude=None):
    found = {}
    for pattern, prefix in [('vmlinuz-*', 'vmlinuz-'), ('kernel-*', 'kernel-')]:
        for path in boot.glob(pattern):
            version = path.name[len(prefix):]
            if path.is_file() and re.fullmatch(r'[A-Za-z0-9_.+-]+', version) and version != exclude:
                initrds = [boot / ('initramfs-' + version + '.img'), boot / ('initrd-' + version),
                           boot / ('initrd.img-' + version)]
                found.setdefault(version, {'version': version, 'kernel': str(path),
                                          'initrd': next((str(p) for p in initrds if p.is_file()), None)})
    # systemd BLS installations store a linux/initrd pair below their entry ID.
    for path in boot.glob('*/*/linux'):
        version = path.parent.name
        if path.is_file() and re.fullmatch(r'[A-Za-z0-9_.+-]+', version) and version != exclude:
            initrd = path.parent / 'initrd'
            found.setdefault(version, {'version': version, 'kernel': str(path),
                                      'initrd': str(initrd) if initrd.is_file() else None})
    for path in Path('/usr/lib/modules').glob('*/vmlinuz'):
        version = path.parent.name
        if boot == Path('/boot') and path.is_file() and version != exclude and re.fullmatch(r'[A-Za-z0-9_.+-]+', version):
            initrd = boot / ('initramfs-' + version + '.img')
            found.setdefault(version, {'version': version, 'kernel': str(path),
                                      'initrd': str(initrd) if initrd.is_file() else None})
    versions = subprocess.run(['sort', '-V'], input='\n'.join(found), text=True,
                              capture_output=True, check=True).stdout.splitlines()[::-1]
    versions.sort(key=lambda v: not any(word in v.lower() for word in ('fiw', 'cachy')))
    return [found[v] for v in versions]


def kernel_cmdline(root):
    config = Path('/etc/kernel/cmdline')
    raw = config.read_text().strip() if config.is_file() else Path('/proc/cmdline').read_text().strip()
    tokens = shlex.split(raw)
    tokens = [token for token in tokens if not token.startswith(('BOOT_IMAGE=', 'initrd=', 'root='))]
    if not root.get('uuid'):
        raise RuntimeError('Cannot identify the target root filesystem UUID.')
    tokens.insert(0, 'root=UUID=' + root['uuid'])
    if root['fstype'] == 'btrfs' and not any(t.startswith('rootflags=') for t in tokens):
        flags = [flag for flag in root.get('options', '').split(',') if flag.startswith('subvol=')]
        if flags:
            tokens.append('rootflags=' + flags[0])
    text = ' '.join(tokens)
    if any(char in text for char in ('\n', '\r', '\0')):
        raise RuntimeError('Invalid kernel command line.')
    return text


def secure_boot():
    files = list(Path('/sys/firmware/efi/efivars').glob('SecureBoot-*'))
    return bool(files and len(files[0].read_bytes()) > 4 and files[0].read_bytes()[4] == 1)


def limine_loader():
    for path in [Path('/usr/share/limine/BOOTX64.EFI'), Path('/usr/share/limine/limine-uefi-cd.bin')]:
        # A CD image is not an EFI executable; only actual PE EFI files qualify.
        if path.is_file() and path.open('rb').read(2) == b'MZ':
            return path
    for path in Path('/usr/share/limine').rglob('BOOTX64.EFI'):
        if path.is_file():
            return path
    raise RuntimeError('Limine BOOTX64.EFI is missing; install sys-boot/limine with uefi-x86-64.')


def render_limine(images, cmdline):
    lines = [BEGIN]
    for image in images:
        version = image['version']
        label = 'custom' if any(word in version.lower() for word in ('fiw', 'cachy')) else 'generic'
        lines += [f'/Gentoo {version} ({label})', '    protocol: linux',
                  f'    path: boot():/{EFI_DIRECTORY}/kernels/{version}/vmlinuz',
                  f'    module_path: boot():/{EFI_DIRECTORY}/kernels/{version}/initramfs.img',
                  '    cmdline: ' + cmdline, '']
    return '\n'.join(lines + [END]) + '\n'


def managed_block(text):
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise RuntimeError('Malformed managed Limine block; preserving the config.')
    if BEGIN not in text:
        return None
    start = text.index(BEGIN)
    end = text.index(END, start) + len(END)
    return text[start:end] + '\n'


def merge_limine(text, block):
    old = managed_block(text)
    if old is None:
        return text.rstrip() + '\n\n' + block if text.strip() else 'timeout: 5\n\n' + block
    return text.replace(old.rstrip('\n'), block.rstrip('\n'), 1)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def block_hash(block):
    return hashlib.sha256(block.encode()).hexdigest() if block else None


def install_config(old):
    values = {'layout': 'compat', 'initrd_generator': 'dracut', 'uki_generator': 'none'}
    lines, seen = [], set()
    for line in old.splitlines():
        key = line.split('=', 1)[0].strip()
        if key in values:
            if key not in seen:
                lines.append(key + '=' + values[key])
                seen.add(key)
        else:
            lines.append(line)
    lines += [key + '=' + value for key, value in values.items() if key not in seen]
    return '\n'.join(lines) + '\n'


def plan(mode, esp=None, exclude=None):
    if mode == 'keep':
        return {'mode': 'keep', 'changes': []}
    if mode not in ('limine', 'grub'):
        raise ValueError('Unknown bootloader')
    if platform.machine() not in ('x86_64', 'amd64') or not Path('/sys/firmware/efi').is_dir():
        raise RuntimeError('Automatic boot deployment supports amd64 UEFI installations.')
    root = mount_info('/')
    if root['fstype'] not in ('ext4', 'btrfs') or root['source'].startswith('/dev/mapper/'):
        raise RuntimeError('Automatic boot deployment currently supports plain ext4/Btrfs roots. Keep the existing loader for encrypted or other layouts.')
    source = re.sub(r'\[.*\]$', '', root['source'])
    device_type = subprocess.run(['lsblk', '--noheadings', '--nodeps', '--output', 'TYPE', source], text=True, capture_output=True)
    if device_type.returncode or device_type.stdout.strip() not in ('part', 'disk'):
        raise RuntimeError('Automatic boot deployment needs a plain disk/partition root; keep the existing loader for this storage layout.')
    target = discover_esp(esp)
    images = kernel_images(exclude=exclude)
    if not images:
        raise RuntimeError('No installed kernel/initramfs candidates found under /boot. Install a distribution kernel first.')
    text = kernel_cmdline(root)
    result = {'mode': mode, 'esp': target, 'root_filesystem': root['fstype'],
              'cmdline': text, 'images': images, 'secure_boot': secure_boot(),
              'firmware': 'preserve current entries/order unless explicitly selected',
              'kernel_refresh_hook': '/etc/kernel/install.d/96-fiw-dots-boot.install'}
    if mode == 'limine':
        result['loader'] = str(limine_loader())
        result['config'] = str(Path(target['path']) / EFI_DIRECTORY / 'limine.conf')
        result['proposed_entries'] = render_limine(images, text)
    else:
        result['config'] = str(GRUB_DIRECTORY / 'grub/grub.cfg')
        result['commands'] = [['grub-install', '--target=x86_64-efi', '--efi-directory=' + target['path'],
                               '--boot-directory=' + str(GRUB_DIRECTORY), '--bootloader-id=Fiw-Gentoo', '--no-nvram'],
                              ['grub-mkconfig', '-o', result['config']]]
    prior = Path('/etc/kernel/install.conf').read_text() if Path('/etc/kernel/install.conf').is_file() else ''
    result['installkernel_config'] = install_config(prior)
    for image in images:
        if not image['initrd']:
            image['generate_initrd'] = '/boot/initramfs-' + image['version'] + '.img'
    return result


def backup(path, root):
    if path.exists() or path.is_symlink():
        target = root / str(path.absolute()).lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target, follow_symlinks=False)


def write(path, content, backups, mode=0o644):
    backup(path, backups)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '.fiw-dots-tmp')
    tmp.write_text(content)
    tmp.chmod(mode)
    tmp.replace(path)


def grub_config(output, images, exclude=None):
    env = dict(os.environ, GRUB_TOP_LEVEL=images[0]['kernel'])
    command = ['grub-mkconfig', '-o', str(output)]
    if not exclude:
        subprocess.run(command, env=env, check=True)
        return
    # Removal hooks can run before the kernel file disappears. Filter discovery
    # through GRUB's library override, without moving installed boot artifacts.
    library = Path('/usr/share/grub')
    source = (library / 'grub-mkconfig_lib').read_text()
    source, count = re.subn(r'\bgrub_file_is_not_garbage\s*\(\s*\)',
                           'fiw_dots_file_is_not_garbage ()', source, count=1)
    if count != 1:
        raise RuntimeError('Cannot filter this GRUB library; preserving the boot menu.')
    paths = ['/boot/kernel-' + exclude] + [prefix + exclude for prefix in
             ('/boot/vmlinuz-', '/vmlinuz-', '/boot/vmlinux-', '/vmlinux-')]
    source += '\ngrub_file_is_not_garbage () {\n case "$1" in\n ' + '|'.join(
        shlex.quote(path) for path in paths) + ') return 1 ;;\n esac\n fiw_dots_file_is_not_garbage "$@"\n}\n'
    with tempfile.TemporaryDirectory(prefix='fiw-dots-grub-') as directory:
        root = Path(directory)
        for path in library.iterdir():
            if path.name != 'grub-mkconfig_lib':
                (root / path.name).symlink_to(path)
        (root / 'grub-mkconfig_lib').write_text(source)
        subprocess.run(command, env=dict(env, pkgdatadir=directory), check=True)


def refresh(saved, backups, exclude=None, ask=None):
    saved.pop('pending_config', None)
    # Recheck the mount every time; never write into an unmounted ESP directory.
    target = discover_esp(Path(saved['esp']))
    images = kernel_images(exclude=exclude)
    if not images:
        raise RuntimeError('No remaining kernels; preserving the boot menu.')
    for image in images:
        if not image['initrd']:
            if not shutil.which('dracut'):
                raise RuntimeError('Missing initramfs for ' + image['version'] + '; install sys-kernel/dracut.')
            path = Path('/boot/initramfs-' + image['version'] + '.img')
            subprocess.run(['dracut', '--force', str(path), image['version']], check=True)
            image['initrd'] = str(path)
    if saved['mode'] == 'grub':
        config = GRUB_DIRECTORY / 'grub/grub.cfg'
        old_hash = file_hash(config)
        output = config
        edited = old_hash and old_hash != saved.get('config_hash')
        replace = edited and ask and ask('Existing GRUB menu differs from the saved version. Replace it with the generated menu?',
                                         ['replace', 'keep'], 'keep') == 'replace'
        if edited and not replace:
            output = config.with_name(config.name + '.new.' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
        else:
            backup(config, backups)
        output.parent.mkdir(parents=True, exist_ok=True)
        for image in images:
            source = Path(image['kernel'])
            if source.parent != Path('/boot'):
                dest = Path('/boot') / ('kernel-' + image['version'])
                if file_hash(dest) != file_hash(source):
                    backup(dest, backups)
                    shutil.copy2(source, dest)
            source = Path(image['initrd'])
            dest = Path('/boot') / ('initramfs-' + image['version'] + '.img')
            if source != dest and not dest.exists():
                shutil.copy2(source, dest)
        scratch = output.with_name('.' + output.name + '.tmp')
        try:
            grub_config(scratch, images, exclude)
            scratch.replace(output)
        finally:
            if scratch.exists():
                scratch.unlink()
        if output != config:
            saved['pending_config'] = str(output)
            print('Preserved edited GRUB config; review ' + str(output))
        else:
            saved['config_hash'] = file_hash(config)
        return saved
    folder = Path(target['path']) / EFI_DIRECTORY
    required = sum(Path(source).stat().st_size for image in images
                   for source, name in [(image['kernel'], 'vmlinuz'), (image['initrd'], 'initramfs.img')]
                   if file_hash(folder / 'kernels' / image['version'] / name) != file_hash(Path(source)))
    if shutil.disk_usage(target['path']).free < required + 16 * 1024 * 1024:
        raise RuntimeError('Not enough free space on the ESP for the selected kernels and initramfs files.')
    for image in images:
        directory = folder / 'kernels' / image['version']
        directory.mkdir(parents=True, exist_ok=True)
        for source, name in [(image['kernel'], 'vmlinuz'), (image['initrd'], 'initramfs.img')]:
            dest = directory / name
            if file_hash(dest) != file_hash(Path(source)):
                backup(dest, backups)
                scratch = dest.with_name('.' + name + '.tmp')
                shutil.copy2(source, scratch)
                scratch.replace(dest)
    config = folder / 'limine.conf'
    old = config.read_text() if config.is_file() else ''
    prior = managed_block(old)
    block = render_limine(images, saved['cmdline'])
    output = merge_limine(old, block)
    edited = prior and block_hash(prior) != saved.get('block_hash')
    replace = edited and ask and ask('Existing Limine entries differ from the saved version. Replace the managed entries?',
                                     ['replace', 'keep'], 'keep') == 'replace'
    if edited and not replace:
        proposal = config.with_name(config.name + '.new.' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'))
        write(proposal, output, backups)
        saved['pending_config'] = str(proposal)
        print('Preserved edited Limine entries; review ' + str(proposal))
    elif output != old:
        write(config, output, backups)
        saved['block_hash'] = block_hash(block)
    return saved


def confirm(prompt, choices, default):
    if not sys.stdin.isatty():
        raise RuntimeError('Interactive confirmation required: ' + prompt)
    while True:
        value = input(prompt + ' [' + '/'.join(choices) + '] (default ' + default + '): ').strip().lower() or default
        if value in choices:
            return value


def firmware_commands(target, mode, loader_path, choice, listing):
    if choice == 'keep':
        return []
    label = 'Fiw-Gentoo-' + mode
    matches = []
    for line in listing.splitlines():
        match = re.match(r'^Boot([0-9A-Fa-f]{4})\*?\s+' + re.escape(label) + r'\s', line)
        if match and target.get('partuuid') and target['partuuid'] in line.lower() and loader_path.lower().replace('/', '\\') in line.lower():
            matches.append(match.group(1))
    if matches:
        if choice == 'add':
            return []
        order = re.search(r'^BootOrder:\s*(.*)$', listing, re.M)
        sequence = [matches[0]] + [item for item in (order.group(1).split(',') if order else [])
                                    if item.upper() != matches[0].upper()]
        return [['efibootmgr', '--bootorder', ','.join(sequence)]]
    return [['efibootmgr', '--create' if choice == 'default' else '--create-only',
             '--disk', target['disk'], '--part', str(target['partition']),
             '--label', label, '--loader', loader_path.replace('/', '\\')]]


def deploy(mode, esp=None, ask=confirm):
    if mode == 'keep':
        print('Keeping the current bootloader.')
        return {'status': 'skipped'}
    if os.geteuid() != 0:
        raise RuntimeError('Boot deployment needs root. Run sudo ./install --deploy-bootloader --selection <file>.')
    proposed = plan(mode, esp)
    if proposed['secure_boot']:
        raise RuntimeError('Secure Boot is active. This unsigned deployment requires a separately configured signing setup.')
    for command in (['grub-install', 'grub-mkconfig'] if mode == 'grub' else []):
        if not shutil.which(command):
            raise RuntimeError('Missing command: ' + command)
    if any(not image['initrd'] for image in proposed['images']) and not shutil.which('dracut'):
        raise RuntimeError('Missing initramfs generator: dracut')
    print(json.dumps(proposed, indent=2))
    firmware = ask('UEFI entry: preserve current order, add a menu entry, or make this loader default?',
                   ['keep', 'add', 'default'], 'keep')
    if firmware != 'keep' and not shutil.which('efibootmgr'):
        raise RuntimeError('Install sys-boot/efibootmgr before registering a firmware entry.')
    loader_path = '/EFI/Fiw-Gentoo/' + ('BOOTX64.EFI' if mode == 'limine' else 'grubx64.efi')
    listing = subprocess.run(['efibootmgr', '--verbose'], text=True, capture_output=True, check=True).stdout if firmware != 'keep' else ''
    commands = firmware_commands(proposed['esp'], mode, loader_path, firmware, listing)
    if commands:
        print('Proposed firmware commands: ' + json.dumps(commands))
    if ask('Deploy the previewed bootloader and kernel refresh hook?', ['deploy', 'cancel'], 'cancel') != 'deploy':
        return {'status': 'cancelled'}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backups = MANAGED / 'backups' / ('boot-' + stamp)
    folder = Path(proposed['esp']['path']) / EFI_DIRECTORY
    if folder.exists():
        shutil.copytree(folder, backups / 'efi-directory', symlinks=True)
    if GRUB_DIRECTORY.exists() and mode == 'grub':
        shutil.copytree(GRUB_DIRECTORY, backups / 'grub-directory', symlinks=True)
    prior = json.loads(STATE.read_text()) if STATE.is_file() else {}
    saved = {'mode': mode, 'esp': proposed['esp']['path'], 'cmdline': proposed['cmdline']}
    if prior.get('mode') == mode and prior.get('esp') == saved['esp']:
        saved.update({key: prior[key] for key in ('config_hash', 'block_hash') if key in prior})
    folder.mkdir(parents=True, exist_ok=True)
    if mode == 'limine':
        loader = folder / 'BOOTX64.EFI'
        backup(loader, backups)
        shutil.copy2(proposed['loader'], loader)
        loader_path = '/EFI/Fiw-Gentoo/BOOTX64.EFI'
    else:
        subprocess.run(proposed['commands'][0], check=True)
        loader_path = '/EFI/Fiw-Gentoo/grubx64.efi'
    saved = refresh(saved, backups, ask=ask)
    pending = saved.pop('pending_config', None)
    if pending and firmware != 'keep':
        commands = []
        firmware = 'keep'
        print('Kept the existing boot menu; firmware entries and order remain unchanged. Review ' + pending)
    # Native installkernel provides versioned /boot kernel/initrd files; our
    # final hook refreshes only the chosen loader's own configuration.
    write(Path('/etc/kernel/install.conf'), proposed['installkernel_config'], backups)
    script = Path('/usr/local/libexec/fiw-dots-boot')
    backup(script, backups)
    script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), script)
    script.chmod(0o755)
    hook = '#!/bin/sh\ncase "$1" in\n add) exec /usr/local/libexec/fiw-dots-boot --refresh ;;\n remove) exec /usr/local/libexec/fiw-dots-boot --refresh --exclude-version "$2" ;;\nesac\n'
    write(Path('/etc/kernel/install.d/96-fiw-dots-boot.install'), hook, backups, 0o755)
    # Traditional Gentoo installkernel uses postinst.d rather than install.d.
    legacy = '#!/bin/sh\nexec /usr/local/libexec/fiw-dots-boot --refresh\n'
    write(Path('/etc/kernel/postinst.d/96-fiw-dots-boot'), legacy, backups, 0o755)
    write(STATE, json.dumps(saved, indent=2) + '\n', backups, 0o600)
    for command in commands:
        subprocess.run(command, check=True)
    report = MANAGED / ('boot-' + stamp + '.json')
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'plan': proposed, 'firmware_choice': firmware,
                                  'backups': str(backups)}, indent=2) + '\n')
    print('Boot deployment finished. Report: ' + str(report))
    return {'status': 'partial' if pending else 'completed', 'mode': mode, 'firmware_choice': firmware,
            'review': [pending] if pending else [],
            'report': str(report), 'backups': str(backups)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--exclude-version')
    args = parser.parse_args()
    if not args.refresh:
        parser.error('Use ./install --boot-plan or --deploy-bootloader for initial setup.')
    if os.geteuid() != 0:
        raise RuntimeError('Kernel refresh requires root.')
    if not STATE.is_file():
        return
    saved = json.loads(STATE.read_text())
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    backups = MANAGED / 'backups' / ('boot-refresh-' + stamp)
    updated = refresh(saved, backups, args.exclude_version)
    updated.pop('pending_config', None)
    write(STATE, json.dumps(updated, indent=2) + '\n', backups, 0o600)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print('Boot refresh: ' + str(error), file=sys.stderr)
        sys.exit(1)
