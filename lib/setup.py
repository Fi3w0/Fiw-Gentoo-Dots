"""Optional repositories, Flatpaks and services for the restoration workflow."""
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPOSITORIES = {
    'guru': 'https://github.com/gentoo-mirror/guru.git',
    'steam-overlay': 'https://github.com/anyc/steam-overlay.git',
}
FLATPAKS = {}
LABELS = {'org.localsend.localsend_app': 'LocalSend', 'org.vinegarhq.Sober': 'Sober'}
for list_file in sorted((Path(__file__).resolve().parents[1] / 'flatpaks').glob('*.list')):
    for line in list_file.read_text().splitlines():
        app = line.strip()
        if not app or app.startswith('#'):
            continue
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]*', app) or app.count('.') < 2:
            raise ValueError('Invalid Flatpak ID in ' + list_file.name)
        FLATPAKS[app] = {'label': LABELS.get(app, app), 'group': list_file.stem}
SERVICES = {
    'audio': {'label': 'PipeWire audio (user)', 'scope': 'user',
              'units': ['pipewire.socket', 'pipewire-pulse.socket', 'wireplumber.service'],
              'packages': ['media-video/pipewire', 'media-video/wireplumber']},
    'network': {'label': 'NetworkManager (system)', 'scope': 'system',
                'units': ['NetworkManager.service'], 'packages': ['net-misc/networkmanager']},
    'bluetooth': {'label': 'Bluetooth (system)', 'scope': 'system',
                  'units': ['bluetooth.service'], 'packages': ['net-wireless/bluez']},
    'power': {'label': 'Power profiles (system)', 'scope': 'system',
              'units': ['power-profiles-daemon.service'], 'packages': ['sys-power/power-profiles-daemon']},
}


def required_repositories(selection):
    names = []
    if any(g in selection['groups'] for g in ('fiw-apps', 'gaming')):
        names.append('guru')
    if 'gaming' in selection['groups']:
        names.append('steam-overlay')
    return names


def existing_repository(name):
    if not shutil.which('portageq'):
        return None
    result = subprocess.run(['portageq', 'get_repo_path', '/', name], text=True,
                            capture_output=True)
    if result.returncode or not result.stdout.strip():
        return None
    path = Path(result.stdout.strip())
    if (path / 'profiles/repo_name').is_file():
        return path
    return None


def repository_config(name, location):
    return (f'[{name}]\nlocation = {location}\nsync-type = git\n'
            f'sync-uri = {REPOSITORIES[name]}\nsync-depth = 1\npriority = 10\n')


def stage_repositories(selection, stage):
    """Fetch missing selected repositories into the temporary resolution root."""
    fetched = {}
    for name in required_repositories(selection):
        if existing_repository(name):
            continue
        if not shutil.which('git'):
            raise RuntimeError('Repository preparation needs Git. Install dev-vcs/git first.')
        path = stage / 'var/db/repos' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        print('Preparing missing repository in temporary storage: ' + name, flush=True)
        subprocess.run(['git', 'clone', '--depth=1', REPOSITORIES[name], str(path)], check=True)
        if (path / 'profiles/repo_name').read_text().strip() != name:
            raise RuntimeError('Unexpected repository identity for ' + name)
        config = stage / 'etc/portage/repos.conf' / ('fiw-dots-' + name + '.conf')
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(repository_config(name, path))
        fetched[name] = path
    return fetched


def publish_repositories(fetched):
    """Adopt verified checkouts only after the installation confirmation."""
    for name, source in fetched.items():
        target = Path('/var/db/repos') / name
        if target.exists():
            raise RuntimeError('Repository destination already exists; preserving it: ' + str(target))
        target.parent.mkdir(parents=True, exist_ok=True)
        scratch = target.with_name('.fiw-dots-' + name + '-' + str(os.getpid()))
        try:
            shutil.copytree(source, scratch, symlinks=True)
            scratch.rename(target)
        finally:
            if scratch.exists():
                shutil.rmtree(scratch)


def write_report(kind, report, system=False):
    state = Path('/var/lib/Fiw-Gentoo-Dots') if system else Path.home() / '.local/state/Fiw-Gentoo-Dots'
    state.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    path = state / (kind + '-' + stamp + '.json')
    path.write_text(json.dumps(report, indent=2) + '\n')
    print('Report: ' + str(path))
    return path


def install_flatpaks(selection, ask):
    if os.geteuid() == 0:
        raise RuntimeError('Install user Flatpaks as the target user, not root.')
    apps = selection.get('flatpaks', [])
    if not apps:
        print('No Flatpaks selected.')
        return
    if not shutil.which('flatpak'):
        raise RuntimeError('Flatpak is missing. Install sys-apps/flatpak or select it through the package workflow.')
    missing = [app for app in apps if subprocess.run(
        ['flatpak', 'info', '--user', app], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL).returncode]
    report = {'selected': apps, 'already_installed': [app for app in apps if app not in missing],
              'installed': [], 'failed': [], 'skipped': []}
    print('User Flatpaks from Flathub: ' + (', '.join(missing) or 'all selected apps already installed'))
    if missing and ask('Install these selected Flatpaks for your user?', ['install', 'skip'], 'install') == 'skip':
        report['skipped'] = missing
    elif missing:
        remote = subprocess.run(['flatpak', 'remote-add', '--user', '--if-not-exists',
                                 'flathub', 'https://flathub.org/repo/flathub.flatpakrepo'])
        if remote.returncode:
            report['failed'] = missing
        else:
            for app in missing:
                result = subprocess.run(['flatpak', 'install', '--user', '--noninteractive',
                                         '--assumeyes', 'flathub', app])
                present = subprocess.run(['flatpak', 'info', '--user', app],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                report['installed' if not result.returncode and not present.returncode else 'failed'].append(app)
    write_report('flatpaks', report)
    print('Missing Flatpaks: ' + (', '.join(report['failed'] + report['skipped']) or 'none'))
    if report['failed']:
        raise RuntimeError('Some Flatpaks did not install; see the report.')


def enable_services(selection, ask):
    system = os.geteuid() == 0
    scope = 'system' if system else 'user'
    units = list(dict.fromkeys(unit for key in selection.get('services', [])
                              if SERVICES[key]['scope'] == scope for unit in SERVICES[key]['units']))
    if not units:
        print('No ' + scope + ' services selected.')
        return
    command = ['systemctl'] + ([] if system else ['--user'])
    report = {'scope': scope, 'selected': units, 'enabled': [], 'missing': [], 'failed': [], 'skipped': []}
    available = []
    for unit in units:
        result = subprocess.run(command + ['show', '--property=LoadState', '--value', unit],
                                text=True, capture_output=True)
        if result.returncode or result.stdout.strip() != 'loaded':
            report['missing'].append(unit)
        else:
            available.append(unit)
    print('Enable at next boot/login: ' + (', '.join(available) or 'none'))
    if available and ask('Enable the selected ' + scope + ' services?', ['enable', 'skip'], 'enable') == 'skip':
        report['skipped'] = available
    else:
        for unit in available:
            result = subprocess.run(command + ['enable', unit])
            report['enabled' if not result.returncode else 'failed'].append(unit)
    write_report('services', report, system)
    print('Missing service units: ' + (', '.join(report['missing']) or 'none'))
    if report['failed']:
        raise RuntimeError('Some services could not be enabled; see the report.')
