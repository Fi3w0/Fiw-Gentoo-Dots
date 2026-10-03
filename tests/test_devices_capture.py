import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rice', REPO / 'lib/rice.py')
rice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rice)
import capture


class DevicesAndCaptureTests(unittest.TestCase):
    def test_named_devices_preserve_independent_choices_and_ask_on_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            desktop = rice.load_selection(profile='fiw-ryzen')
            portable = rice.load_selection()
            portable.update(groups=['cli'], configs=['fish', 'neovim'], extras=[])
            rice.device_presets.save(repo, 'desktop', desktop, lambda *args: 'keep')
            rice.device_presets.save(repo, 'portable', portable, lambda *args: 'keep')
            original = rice.device_presets.path(repo, 'desktop').read_bytes()
            rice.device_presets.save(repo, 'desktop', portable, lambda *args: 'keep')
            self.assertEqual(rice.device_presets.path(repo, 'desktop').read_bytes(), original)
            devices = rice.device_presets.list_presets(repo, rice.load_selection)
            self.assertEqual(devices['desktop']['profile'], 'fiw-ryzen')
            self.assertEqual(devices['portable']['configs'], ['fish', 'neovim'])
            self.assertEqual(devices['portable']['name'], 'portable')
            self.assertEqual(rice.device_presets.path(repo, 'portable').stat().st_mode & 0o777, 0o600)
            rice.device_presets.save(repo, 'desktop', portable, lambda *args: 'save')
            self.assertEqual(rice.device_presets.list_presets(repo, rice.load_selection)['desktop']['profile'], 'stock')

    def test_unsafe_names_and_invalid_local_selections_do_not_enter_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            root = repo / 'local/devices'; root.mkdir(parents=True)
            for content in ('[]', '{"profile":"stock"}', '{broken'):
                (root / 'broken.json').write_text(content)
                self.assertEqual(rice.device_presets.list_presets(repo, rice.load_selection), {})
            for name in ('../escape', '/escape', '-name', 'Desktop', 'a'*49):
                with self.assertRaises(ValueError):
                    rice.device_presets.save(repo, name, rice.load_selection(), lambda *args: 'save')
            (root / 'linked.json').symlink_to(repo / 'outside.json')
            with self.assertRaises(RuntimeError):
                rice.device_presets.save(repo, 'linked', rice.load_selection(), lambda *args: 'save')
            self.assertFalse((repo / 'outside.json').exists())

    def test_selective_portable_capture_needs_no_other_app_or_kde_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home, repo = root / 'home', root / 'repo'
            source = home / '.config/kitty/kitty.conf'; source.parent.mkdir(parents=True)
            source.write_text('foreground #abcdef\nlinux_display_server wayland\n')
            unrelated = repo / 'configs/fish/files/.config/fish/conf.d/fiw.fish'
            unrelated.parent.mkdir(parents=True); unrelated.write_text('keep existing capture\n')
            with patch.object(capture, 'HOME', home), patch.object(capture, 'REPO', repo):
                capture.capture(['kitty'])
            target = repo / 'configs/kitty/files/.config/kitty/kitty.conf'
            self.assertIn('linux_display_server auto', target.read_text())
            self.assertEqual(unrelated.read_text(), 'keep existing capture\n')
            self.assertEqual({path.relative_to(repo).parts[1] for path in repo.rglob('*') if path.is_file()}, {'kitty','fish'})

    def test_shortcuts_capture_keeps_style_and_drops_device_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home, repo = root / 'home', root / 'repo'
            source = home / '.config/kwinrc'; source.parent.mkdir(parents=True)
            source.write_text('[Desktops]\nNumber=1\nRows=1\nId_1=device-only\n[org.kde.kdecoration2]\ntheme=local\n')
            style = repo / 'configs/kde-style/kconfig/.config/kwinrc'
            style.parent.mkdir(parents=True); style.write_text('captured style stays intact\n')
            with patch.object(capture, 'HOME', home), patch.object(capture, 'REPO', repo):
                capture.capture(['kde-shortcuts'])
            result = (repo / 'configs/kde-shortcuts/kconfig/.config/kwinrc').read_text()
            self.assertIn('Number=1',result)
            self.assertNotIn('device-only',result)
            self.assertNotIn('theme=local',result)
            self.assertEqual(style.read_text(), 'captured style stays intact\n')

    def test_vscode_capture_reads_jsonc_and_omits_machine_settings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home, repo = root / 'home', root / 'repo'
            source = home / '.config/Code/User/settings.json'; source.parent.mkdir(parents=True)
            source.write_text('{ // comment\n"workbench.colorTheme":"ayu MiDas", /* comment */\n"claudeCode.selectedModel":"literal//comma,}",\n"java.configuration.runtimes":[{"path":"device-only"}], "unrelatedSecret":"keep-local",}')
            with patch.object(capture, 'HOME', home), patch.object(capture, 'REPO', repo):
                capture.capture(['vscode'])
            result = json.loads((repo / 'configs/vscode/json/.config/Code/User/settings.json').read_text())
            self.assertEqual(result, {'workbench.colorTheme':'ayu MiDas','claudeCode.selectedModel':'literal//comma,}'})

    def test_restore_then_recapture_keeps_helpers_portable_and_does_not_nest_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home, repo = root / 'home', root / 'repo'
            home.mkdir()
            selection = rice.load_selection()
            selection.update(groups=[], configs=['fish', 'kde-shortcuts'])
            rice.apply_configs(selection, home, conflict='apply')
            with patch.object(capture, 'HOME', home), patch.object(capture, 'REPO', repo):
                capture.capture(['fish', 'kde-shortcuts'])
            fish = (repo / 'configs/fish/files/.config/fish/conf.d/fiw.fish').read_text()
            self.assertEqual(fish.count('if type -q fiw-update'), 1)
            desktop = (repo / 'configs/kde-shortcuts/files/.local/share/applications/net.local.fiw-shot-region.desktop').read_text()
            self.assertIn('Exec="{{HOME}}/.local/bin/fiw-shot" region', desktop)
            self.assertNotIn(str(home), desktop)

    def test_vscode_restore_merges_jsonc_and_keeps_local_runtime_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            target = home / '.config/Code/User/settings.json'
            target.parent.mkdir(parents=True)
            target.write_text('{ // local preference comment\n"privatePreference":"local-only",\n"java.configuration.runtimes":[{"path":"device-only"}],}')
            selection = rice.load_selection(); selection.update(groups=[], configs=['vscode'])
            rice.apply_configs(selection, home, conflict='apply')
            result = json.loads(target.read_text())
            self.assertEqual(result['privatePreference'], 'local-only')
            self.assertEqual(result['java.configuration.runtimes'], [{'path':'device-only'}])
            self.assertEqual(result['workbench.colorTheme'], 'ayu MiDas')


if __name__ == '__main__':
    unittest.main()
