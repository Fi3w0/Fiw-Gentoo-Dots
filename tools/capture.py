#!/usr/bin/env python3
"""Capture explicitly selected preferences, never whole application profiles."""
import argparse
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()
APP_KEYS = {
    'ark': ('.config/arkrc', {
        '[Extraction]': ['openDestinationFolderAfterExtraction'],
        '[General]': ['LockSidebar', 'ShowSidebar'], '[MainWindow]': ['StatusBar']}),
    'gwenview': ('.config/gwenviewrc', {
        '[MainWindow]': ['MenuBar'], '[SideBar]': ['InformationSplitterSizes']}),
    'prism': ('.local/share/PrismLauncher/prismlauncher.cfg', {'[General]': [
        'ApplicationTheme', 'IconTheme', 'ConsoleFont', 'ConsoleFontSize',
        'ConsoleMaxLines', 'ConsoleOverflowStop', 'ShowConsole', 'ShowConsoleOnError',
        'AutoCloseConsole', 'CloseAfterLaunch', 'QuitAfterGameStop', 'RecordGameTime',
        'ShowGameTime', 'ShowGameTimeWithoutDays', 'ShowGlobalGameTime',
        'MenuBarInsteadOfToolBar', 'StatusBarVisible', 'ToolbarsLocked']})}


def read_jsonc(text):
    # Keep quoted strings intact while removing comments and trailing commas.
    text = re.sub(r'"(?:[^"\\]|\\.)*"|//[^\r\n]*|/\*[\s\S]*?\*/',
                  lambda match: match[0] if match[0].startswith('"') else
                  re.sub(r'[^\r\n]', ' ', match[0]), text)
    text = re.sub(r'"(?:[^"\\]|\\.)*"|,(?=\s*[}\]])',
                  lambda match: match[0] if match[0].startswith('"') else '', text)
    return json.loads(text)


def sections(text):
    result, group = {}, None
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            group = line
            result.setdefault(group, {})
        elif group and "=" in line and not line.startswith(("#", ";")):
            key, value = line.split("=", 1)
            result[group][key] = value
    return result


def write(path, text):
    dest = REPO / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text)


def kconfig(name, relative, groups=None, keys=None):
    src = HOME / relative
    if not src.is_file():
        return
    data = sections(src.read_text())
    if groups is not None:
        data = {g: v for g, v in data.items() if g in groups}
    if keys:
        data = {g: {k: v for k, v in values.items() if k in keys.get(g, ())}
                for g, values in data.items() if g in keys}
    for g in list(data):
        if re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", g):
            del data[g]
            continue
        data[g] = {k: v for k, v in data[g].items()
                   if not re.search(r"/home/|/run/user/|[0-9a-f]{8}-[0-9a-f]{4}-", k + v)}
    write(f"configs/{name}/kconfig/{relative}",
          "\n\n".join(g + "\n" + "\n".join(k + "=" + v for k, v in values.items())
                      for g, values in data.items() if values) + "\n")


def copy(name, relative, transform=None):
    src = HOME / relative
    if not src.is_file():
        return
    text = src.read_text()
    if transform:
        text = transform(text)
    write(f"configs/{name}/files/{relative}", text)
    dest = REPO / f"configs/{name}/files/{relative}"
    dest.chmod(src.stat().st_mode & 0o777)


def copy_assets(source, destination):
    for src in source.rglob('*'):
        dest = destination / src.relative_to(source)
        if src.is_dir() and not src.is_symlink():
            dest.mkdir(parents=True, exist_ok=True)
        elif src.is_symlink():
            dest.parent.mkdir(parents=True, exist_ok=True)
            target = src.readlink()
            if dest.is_symlink() and dest.readlink() == target:
                continue
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.symlink_to(target)
        elif src.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)


CAPTURE_IDS = tuple(sorted(set(APP_KEYS) | {
    'kde-style', 'kde-shortcuts', 'dolphin', 'spectacle', 'fish', 'kitty',
    'neovim', 'fastfetch', 'mangohud', 'vscode', 'vesktop', 'autostart'}))


def capture_apps(selected=None):
    for name, (relative, keys) in APP_KEYS.items():
        if selected is None or name in selected:
            kconfig(name, relative, keys=keys)


def capture_style():
    if (HOME / ".config/kdeglobals").is_file():
        kconfig("kde-style", ".config/kdeglobals",
                groups=[g for g in sections((HOME / '.config/kdeglobals').read_text())
                        if g.startswith(('[Colors:', '[ColorEffects:'))]
                       + ['[General]', '[Icons]', '[KDE]', '[WM]'])
        p = REPO / 'configs/kde-style/kconfig/.config/kdeglobals'
        p.write_text('\n'.join(line for line in p.read_text().splitlines()
                               if not line.startswith(('ColorSchemeHash=', 'LastUsedCustomAccentColor=',
                                                         'TerminalApplication=', 'TerminalService='))) + '\n')
    gtk_keys = ['gtk-theme-name', 'gtk-icon-theme-name', 'gtk-font-name',
                'gtk-cursor-theme-name', 'gtk-cursor-theme-size',
                'gtk-application-prefer-dark-theme']
    for version in ['3.0', '4.0']:
        for name in ['gtk.css', 'colors.css']:
            copy('kde-style', f'.config/gtk-{version}/{name}')
        relative = f'.config/gtk-{version}/settings.ini'
        kconfig('kde-style', relative, keys={'[Settings]': gtk_keys})
        dest = REPO / 'configs/kde-style/kconfig' / relative
        if dest.is_file() and (HOME / relative).is_file():
            dest.write_text(dest.read_text().replace('gtk-cursor-theme-name=Qogir',
                                                     'gtk-cursor-theme-name=Fiw-Qogir'))
    kconfig('kde-style', '.config/kcminputrc', keys={'[Mouse]': ['cursorTheme']})
    kconfig('kde-style', '.config/kwinrc', groups=['[org.kde.kdecoration2]'])
    copy('kde-style', '.local/share/color-schemes/GentooPurple.colors')
    # These small upstream assets retain their original licence notices.
    theme = HOME / '.local/share/aurorae/themes/Utterly-Round-Dark'
    if theme.is_dir():
        copy_assets(theme, REPO / 'configs/kde-style/files/.local/share/aurorae/themes/Utterly-Round-Dark')
    cursor = HOME / '.local/share/icons/Qogir'
    if (cursor / 'cursors').is_dir():
        dest = REPO / 'configs/kde-style/files/.local/share/icons/Fiw-Qogir'
        copy_assets(cursor / 'cursors', dest / 'cursors')
        shutil.copy2(cursor / 'COPYING', dest / 'COPYING')
        (dest / 'index.theme').write_text('[Icon Theme]\nName=Fiw Qogir\nComment=Qogir cursors\nInherits=breeze_cursors\n')
        p = REPO / 'configs/kde-style/kconfig/.config/kcminputrc'
        if p.is_file() and (HOME / '.config/kcminputrc').is_file():
            p.write_text(p.read_text().replace('cursorTheme=Qogir', 'cursorTheme=Fiw-Qogir'))


def capture_dolphin():
    kconfig('dolphin', '.config/dolphinrc', groups=['[KFileDialog Settings]', '[MainWindow]'])
    kconfig('dolphin', '.local/state/dolphinstaterc', keys={'[FilterBar]': ['caseSensitive', 'filterMode'], '[State]': ['State']})
    kconfig('dolphin', '.config/kwinrulesrc', groups=['[fiw-dolphin-opacity]'])
    if (HOME / '.config/kwinrulesrc').is_file():
        write('configs/dolphin/kconfig/.config/kwinrulesrc',
              '[General]\nrules=fiw-dolphin-opacity\ncount=1\n\n' +
              (REPO / 'configs/dolphin/kconfig/.config/kwinrulesrc').read_text())
    copy('dolphin', '.local/share/kxmlgui5/dolphin/dolphinui.rc')


def capture_shortcuts():
    kconfig('kde-shortcuts', '.config/kglobalshortcutsrc')
    kconfig('kde-shortcuts', '.config/kxkbrc', groups=['[Layout]'])
    kconfig('kde-shortcuts', '.config/kwinrc', keys={'[Desktops]': ['Number', 'Rows']})
    for name in ['net.local.kitty.desktop', 'net.local.fiw-shot-region.desktop', 'net.local.fiw-shot-screen.desktop']:
        copy('kde-shortcuts', '.local/share/applications/' + name,
             lambda t: re.sub(r'(?m)^Exec=("?)' + re.escape(str(HOME)) + r'/.local/bin/fiw-shot\1',
                              'Exec="{{HOME}}/.local/bin/fiw-shot"', t))
    copy('kde-shortcuts', '.local/bin/fiw-shot')


def capture_fish():
    copy('fish', '.config/fish/conf.d/fiw.fish',
         lambda t: t if 'if type -q fiw-update' in t else
         t.replace("alias update='sudo fiw-update'",
                   "if type -q fiw-update\n    alias update='sudo fiw-update'\nend"))
    copy('fish', '.config/fish/conf.d/done.fish')


def capture_kitty():
    def portable_profile(text, name):
        text = re.sub(r'(?m)^linux_display_server\s+wayland\s*$',
                      'linux_display_server auto', text)
        text = re.sub(r'(?m)^shell\s+.*\n?', '', text)
        if name == 'kitty-common.conf':
            text = text.rstrip() + '\n\nshell fish\n'
        return text
    for name in ['kitty.conf', 'kitty-main.conf', 'kitty-bright.conf', 'kitty-common.conf']:
        copy('kitty', '.config/kitty/' + name,
             lambda t: portable_profile(t, name))


def capture_neovim():
    def load_bundled_theme(text):
        if 'vim.cmd.packadd' not in text:
            text = '-- Load the bundled native theme package.\npcall(vim.cmd.packadd, "catppuccin")\n' + text
        return text
    copy('neovim', '.config/nvim/init.lua', load_bundled_theme)


def capture_fastfetch():
    if not (HOME / '.config/fastfetch/config.jsonc').is_file():
        return
    # Keep the layout; the built-in Gentoo logo also works outside Kitty.
    data = read_jsonc((HOME / '.config/fastfetch/config.jsonc').read_text())
    data['logo'] = {'source': 'gentoo', 'type': 'builtin',
                    'padding': data.get('logo', {}).get('padding', {})}
    for module in data.get('modules', []):
        if isinstance(module, dict):
            if isinstance(module.get('format'), str):
                module['format'] = module['format'].replace('\\u001b', '\x1b')
            if module.get('type') == 'os':
                module['key'] = module.get('key', '').replace('', '')
    write('configs/fastfetch/files/.config/fastfetch/config.jsonc', json.dumps(data, indent=2) + '\n')


def capture_mangohud():
    for name in ['MangoHud.conf', 'presets.conf']:
        copy('mangohud', '.config/MangoHud/' + name)


def capture_vscode():
    source = HOME / '.config/Code/User/settings.json'
    if not source.is_file():
        return
    data = read_jsonc(source.read_text())
    keys = ['workbench.colorTheme', 'claudeCode.preferredLocation',
            'redhat.telemetry.enabled', 'claudeCode.selectedModel',
            'explorer.confirmDelete', 'python.languageServer', 'git.autofetch',
            'explorer.confirmDragAndDrop', 'docker.extension.dockerEngineAvailabilityPrompt']
    write('configs/vscode/json/.config/Code/User/settings.json',
          json.dumps({key: data[key] for key in keys if key in data}, indent=2) + '\n')


def capture_vesktop():
    if (HOME / '.config/vesktop/settings.json').is_file():
        # Explicit preference fields: cloud credentials, sessions and caches excluded.
        data = json.loads((HOME / '.config/vesktop/settings.json').read_text())
        allowed = ['discordBranch', 'minimizeToTray', 'arRPC', 'splashColor', 'splashBackground',
                   'autoStartMinimized', 'customTitleBar', 'splashPixelated']
        data = {k: data[k] for k in allowed if k in data}
        if isinstance(data.get('splashBackground'), str) and '/home/' in data['splashBackground']:
            data.pop('splashBackground')
        write('configs/vesktop/json/.config/vesktop/settings.json', json.dumps(data, indent=2) + '\n')
    if (HOME / '.config/vesktop/settings/settings.json').is_file():
        data = json.loads((HOME / '.config/vesktop/settings/settings.json').read_text())
        allowed = ['autoUpdate', 'autoUpdateNotification', 'useQuickCss', 'eagerPatches',
                   'frameless', 'transparent', 'winCtrlQ', 'disableMinSize', 'winNativeTitleBar']
        prefs = {k: data[k] for k in allowed if k in data}
        theme_root = REPO / 'configs/vesktop/files/.config/vesktop/themes'
        prefs['enabledThemes'] = [name for name in data.get('enabledThemes', [])
                                  if Path(name).name == name and (theme_root / name).is_file()]
        prefs['plugins'] = {name: {'enabled': plugin['enabled']}
                            for name, plugin in data.get('plugins', {}).items()
                            if isinstance(plugin, dict) and isinstance(plugin.get('enabled'), bool)}
        write('configs/vesktop/json/.config/vesktop/settings/settings.json',
              json.dumps(prefs, indent=2) + '\n')


def capture_autostart():
    for name in ['steam', 'spotify', 'vesktop', 'opendeck', 'musicpresence']:
        copy('autostart', '.config/autostart/' + name + '.desktop')
    kconfig('autostart', '.config/kwinrulesrc', groups=[
        '[fiw-autostart-minimized-discord]', '[fiw-autostart-minimized-opendeck]',
        '[fiw-autostart-minimized-spotify]'])
    p = REPO / 'configs/autostart/kconfig/.config/kwinrulesrc'
    if (HOME / '.config/kwinrulesrc').is_file():
        p.write_text('[General]\nrules=fiw-autostart-minimized-discord,fiw-autostart-minimized-opendeck,fiw-autostart-minimized-spotify\ncount=3\n\n' + p.read_text())


def capture(selected=None):
    selected = set(CAPTURE_IDS if selected is None else selected)
    if selected - set(CAPTURE_IDS):
        raise ValueError('Unknown capture selection: ' + ', '.join(sorted(selected - set(CAPTURE_IDS))))
    capture_apps(selected)
    functions = {'kde-style': capture_style, 'kde-shortcuts': capture_shortcuts,
                 'dolphin': capture_dolphin, 'fish': capture_fish, 'kitty': capture_kitty,
                 'neovim': capture_neovim, 'fastfetch': capture_fastfetch,
                 'mangohud': capture_mangohud, 'vscode': capture_vscode,
                 'vesktop': capture_vesktop, 'autostart': capture_autostart}
    for name in sorted(selected):
        if name in functions:
            functions[name]()
        elif name == 'spectacle':
            kconfig('spectacle', '.config/spectaclerc', groups=['[General]', '[Annotations]'])
    print('Captured: ' + ', '.join(sorted(selected)))
    print('Review the diff and run tools/check-private.py before committing.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument('--apps-only', action='store_true', help='Recapture only Ark, Gwenview and Prism preferences')
    choice.add_argument('--config', nargs='+', choices=CAPTURE_IDS, help='Recapture only these configs')
    parser.add_argument('--list', action='store_true', help='List supported capture selections')
    parser.add_argument('--home', type=Path, default=HOME, help='Read preferences from this home directory')
    args = parser.parse_args()
    HOME = args.home.resolve()
    if args.list:
        print('\n'.join(CAPTURE_IDS))
    else:
        capture(APP_KEYS if args.apps_only else args.config)
