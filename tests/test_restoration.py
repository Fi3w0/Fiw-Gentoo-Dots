import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('rice', Path(__file__).resolve().parents[1] / 'lib/rice.py')
rice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rice)


class RestorationTests(unittest.TestCase):
    def test_app_capture_uses_explicit_preferences_and_omits_accounts_and_paths(self):
        import capture
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, repo = root / 'home', root / 'repo'
            source = home / '.local/share/PrismLauncher/prismlauncher.cfg'
            source.parent.mkdir(parents=True)
            source.write_text('[General]\nApplicationTheme=Breeze\nIconTheme=breeze_dark\nSelectedInstance=local-instance\nJavaPath=/device/java\nModrinthToken=local-only\n[Accounts]\nuser=local-user\n')
            with patch.object(capture, 'HOME', home), patch.object(capture, 'REPO', repo):
                capture.capture_apps()
            result = (repo / 'configs/prism/kconfig/.local/share/PrismLauncher/prismlauncher.cfg').read_text()
            self.assertEqual(result, '[General]\nApplicationTheme=Breeze\nIconTheme=breeze_dark\n')

    def test_config_requirements_do_not_select_packages_and_report_actual_missing_apps(self):
        selection = rice.load_selection()
        selection.update(groups=[], configs=['kitty'], extras=[], bootloader='keep')
        with patch.object(rice.shutil, 'which', return_value='portageq'), patch.object(rice.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            requirements = rice.config_requirements(selection)
            self.assertEqual(requirements['kitty'], [{'package': 'x11-terms/kitty', 'status': 'missing'}])
            self.assertEqual(rice.package_map(selection), {})
            selection['groups'] = ['fiw-apps']
            self.assertEqual(rice.config_requirements(selection)['kitty'][0]['status'], 'selected')
            self.assertEqual(rice.config_requirements(selection, planned=False)['kitty'][0]['status'], 'missing')

    def test_backup_restore_preserves_current_file_and_future_updates_preserve_restored_edits(self):
        selection = rice.load_selection()
        selection.update(groups=[], configs=['fastfetch'])
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.backups.os, 'geteuid', return_value=1000):
            home = Path(temp)
            target = home / '.config/fastfetch/config.jsonc'
            target.parent.mkdir(parents=True)
            target.write_text('original personal config\n')
            rice.apply_configs(selection, home, conflict='apply')
            current = target.read_text()
            choices = rice.backups.list_backups(home, rice.backup_paths())
            self.assertEqual(len(choices), 1)
            report = rice.backups.restore(home, choices[0]['id'], rice.backup_paths(), lambda *args: 'restore', lambda *args: False, conflict='apply')
            self.assertEqual(target.read_text(), 'original personal config\n')
            saved = rice.backups.user_state(home) / 'backups' / report['current_backup'] / '.config/fastfetch/config.jsonc'
            self.assertEqual(saved.read_text(), current)
            rice.apply_configs(selection, home, update=True, conflict='apply')
            self.assertEqual(target.read_text(), 'original personal config\n')
            self.assertTrue(Path(str(target) + '.new').is_file())

    def test_backup_preview_rejects_unknown_paths_and_destinations_outside_home(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home, outside = root / 'home', root / 'outside'
            home.mkdir(); outside.mkdir()
            backup_id = '20260101T000000.000000Z'
            backup = rice.backups.user_state(home) / 'backups' / backup_id
            source = backup / '.config/fastfetch/config.jsonc'
            source.parent.mkdir(parents=True); source.write_text('previous')
            (home / '.config').symlink_to(outside, target_is_directory=True)
            with self.assertRaises(RuntimeError):
                rice.backups.plan(home, backup_id, rice.backup_paths())
            (home / '.config').unlink()
            (backup / 'unrecognized').write_text('unrecognized')
            with self.assertRaises(RuntimeError):
                rice.backups.plan(home, backup_id, rice.backup_paths())
            self.assertEqual(list(outside.iterdir()), [])

    def test_shared_config_backup_keeps_original_before_all_selected_patches(self):
        selection = rice.load_selection()
        selection['configs'] = ['kde-style', 'kde-shortcuts']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home = root / 'home'; home.mkdir()
            relative = Path('.config/kwinrc')
            target = home / relative; target.parent.mkdir()
            original = '[Appearance]\ncolour=orange\n[Desktops]\nNumber=4\n'
            target.write_text(original)
            style, shortcuts = root / 'style', root / 'shortcuts'
            style.write_text('[Appearance]\ncolour=purple\n')
            shortcuts.write_text('[Desktops]\nNumber=1\n')
            entries = [('kde-style', 'kconfig', style, relative), ('kde-shortcuts', 'kconfig', shortcuts, relative)]
            with patch.object(rice, 'config_entries', return_value=entries):
                rice.apply_configs(selection, home, conflict='apply')
            saved = list((rice.backups.user_state(home) / 'backups').rglob('kwinrc'))
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].read_text(), original)
            self.assertIn('colour=purple', target.read_text())
            self.assertIn('Number=1', target.read_text())

    def test_combined_report_correlates_scopes_and_excludes_unrelated_runs(self):
        selection = rice.load_selection()
        selection.update(groups=['gaming'], configs=['fastfetch'], flatpaks=['org.vinegarhq.Sober'], services=['audio'])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home = root / 'home'; home.mkdir()
            with patch.object(rice.reporting, 'SYSTEM_STATE', root / 'system'):
                with patch.object(rice.reporting.os, 'geteuid', return_value=0):
                    rice.reporting.record(selection, 'current', 'packages', home, {'present': ['app-misc/fastfetch'], 'skipped': ['games-util/example'], 'missing': ['games-util/example']})
                with patch.object(rice.reporting.os, 'geteuid', return_value=1000):
                    rice.reporting.record(selection, 'current', 'flatpaks', home, {'failed': ['org.vinegarhq.Sober']}, RuntimeError('download failed'))
                    rice.reporting.record(selection, 'different', 'configs', home, {'applied': ['unrelated-file']})
                    result = rice.reporting.summarize(selection, home, {}, ['manual reminder'], 'current')
                self.assertEqual(result['steps']['packages']['status'], 'partial')
                self.assertEqual(result['steps']['flatpaks']['status'], 'failed')
                self.assertEqual(result['steps']['configs']['status'], 'not attempted')
                self.assertEqual(result['steps']['services-user']['status'], 'not attempted')
                self.assertNotIn('unrelated-file', json.dumps(result))
                self.assertEqual(result['manual_steps'], ['manual reminder'])


if __name__ == '__main__':
    unittest.main()
