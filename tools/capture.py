#!/usr/bin/env python3
"""Capture explicitly selected preferences, never whole application profiles."""
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()


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


def capture():
    kconfig("kde-style", ".config/kdeglobals",
            groups=[g for g in sections((HOME / '.config/kdeglobals').read_text())
                    if g.startswith(('[Colors:', '[ColorEffects:'))]
                   + ['[General]', '[Icons]', '[KDE]', '[WM]'])
    p = REPO / 'configs/kde-style/kconfig/.config/kdeglobals'
    p.write_text('\n'.join(line for line in p.read_text().splitlines()
                           if not line.startswith(('ColorSchemeHash=', 'LastUsedCustomAccentColor='))) + '\n')
    kconfig('kde-style', '.config/kcminputrc', keys={'[Mouse]': ['cursorTheme']})
    kconfig('kde-style', '.config/kwinrc', groups=['[org.kde.kdecoration2]'])
    kconfig('dolphin', '.config/dolphinrc', groups=['[KFileDialog Settings]', '[MainWindow]'])
    kconfig('dolphin', '.local/state/dolphinstaterc', keys={'[FilterBar]': ['caseSensitive', 'filterMode'], '[State]': ['State']})
    kconfig('dolphin', '.config/kwinrulesrc', groups=['[fiw-dolphin-opacity]'])
    write('configs/dolphin/kconfig/.config/kwinrulesrc',
          '[General]\nrules=fiw-dolphin-opacity\ncount=1\n\n' +
          (REPO / 'configs/dolphin/kconfig/.config/kwinrulesrc').read_text())
    copy('dolphin', '.local/share/kxmlgui5/dolphin/dolphinui.rc')
    copy('kde-style', '.local/share/color-schemes/GentooPurple.colors')
    kconfig('kde-shortcuts', '.config/kglobalshortcutsrc')
    kconfig('kde-shortcuts', '.config/kxkbrc', groups=['[Layout]'])
    for name in ['net.local.kitty.desktop', 'net.local.fiw-shot-region.desktop', 'net.local.fiw-shot-screen.desktop']:
        copy('kde-shortcuts', '.local/share/applications/' + name,
             lambda t: t.replace('Exec=' + str(HOME) + '/.local/bin/fiw-shot', 'Exec="{{HOME}}/.local/bin/fiw-shot"'))
    copy('kde-shortcuts', '.local/bin/fiw-shot')
    kconfig('spectacle', '.config/spectaclerc', groups=['[General]', '[Annotations]'])
    copy('fish', '.config/fish/conf.d/fiw.fish',
         lambda t: t.replace("alias update='sudo fiw-update'",
                             "if type -q fiw-update\n    alias update='sudo fiw-update'\nend"))
    copy('fish', '.config/fish/conf.d/done.fish')
    for name in ['kitty.conf', 'kitty-main.conf', 'kitty-bright.conf', 'kitty-common.conf']:
        copy('kitty', '.config/kitty/' + name)
    copy('neovim', '.config/nvim/init.lua')
    # Keep the layout; the built-in Gentoo logo also works outside Kitty.
    data = json.loads((HOME / '.config/fastfetch/config.jsonc').read_text())
    data['logo'] = {'source': 'gentoo', 'type': 'builtin',
                    'padding': data.get('logo', {}).get('padding', {})}
    for module in data.get('modules', []):
        if isinstance(module, dict):
            if isinstance(module.get('format'), str):
                module['format'] = module['format'].replace('\\u001b', '\x1b')
            if module.get('type') == 'os':
                module['key'] = module.get('key', '').replace('', '')
    write('configs/fastfetch/files/.config/fastfetch/config.jsonc', json.dumps(data, indent=2) + '\n')
    for name in ['MangoHud.conf', 'presets.conf']:
        copy('mangohud', '.config/MangoHud/' + name)
    copy('vscode', '.config/Code/User/settings.json')
    # Explicit preference fields: cloud credentials, sessions and caches excluded.
    data = json.loads((HOME / '.config/vesktop/settings.json').read_text())
    allowed = ['discordBranch', 'minimizeToTray', 'arRPC', 'splashColor', 'splashBackground',
               'autoStartMinimized', 'customTitleBar', 'splashPixelated']
    data = {k: data[k] for k in allowed if k in data}
    if isinstance(data.get('splashBackground'), str) and '/home/' in data['splashBackground']:
        data.pop('splashBackground')
    write('configs/vesktop/json/.config/vesktop/settings.json', json.dumps(data, indent=2) + '\n')
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
    for name in ['steam', 'spotify', 'vesktop', 'opendeck', 'musicpresence']:
        copy('autostart', '.config/autostart/' + name + '.desktop')
    kconfig('autostart', '.config/kwinrulesrc', groups=[
        '[fiw-autostart-minimized-discord]', '[fiw-autostart-minimized-opendeck]',
        '[fiw-autostart-minimized-spotify]'])
    p = REPO / 'configs/autostart/kconfig/.config/kwinrulesrc'
    p.write_text('[General]\nrules=fiw-autostart-minimized-discord,fiw-autostart-minimized-opendeck,fiw-autostart-minimized-spotify\ncount=3\n\n' + p.read_text())
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
        p.write_text(p.read_text().replace('cursorTheme=Qogir', 'cursorTheme=Fiw-Qogir'))
    print('Captured selected preferences. Review the diff and run tools/check-private.py before committing.')


if __name__ == '__main__':
    capture()
