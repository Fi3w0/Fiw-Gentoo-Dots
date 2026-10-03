import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('rice', Path(__file__).resolve().parents[1] / 'lib/rice.py')
rice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rice)


class ConfigTests(unittest.TestCase):
    def test_kconfig_preserves_unrelated_state_and_combines_window_rules(self):
        old = '# comment\n[General]\nrules=my-rule\ncount=1\nkeep=value\n[Session]\nprivate=preserved\n'
        desired = '[General]\nrules=fiw-dolphin-opacity\ncount=1\n[Style]\ncolour=purple\n'
        result = rice.merge_kconfig(old, desired)
        self.assertIn('# comment', result)
        self.assertIn('private=preserved', result)
        self.assertIn('keep=value', result)
        self.assertIn('rules=my-rule,fiw-dolphin-opacity', result)
        self.assertIn('count=2', result)
        self.assertEqual(rice.merge_kconfig(result, desired), result)

    def test_json_merge_preserves_account_and_unrelated_preferences(self):
        old = '{"session": "existing", "nested": {"unrelated": 1, "selected": 2}}'
        desired = '{"nested": {"selected": 3}}'
        self.assertEqual(json.loads(rice.merge_json(old, desired)),
                         {'session': 'existing', 'nested': {'unrelated': 1, 'selected': 3}})

    def test_conflicts_backup_and_updates_preserve_local_edits(self):
        selection = rice.load_selection()
        selection['configs'] = ['fastfetch']
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            target = home / '.config/fastfetch/config.jsonc'
            target.parent.mkdir(parents=True)
            target.write_text('original local config\n')
            kept = rice.apply_configs(selection, home, conflict='keep')
            self.assertEqual(target.read_text(), 'original local config\n')
            self.assertEqual(len(kept['kept']), 1)
            rice.apply_configs(selection, home, conflict='apply')
            backups = list((home / '.local/state/Fiw-Gentoo-Dots/backups').rglob('config.jsonc'))
            self.assertEqual(backups[0].read_text(), 'original local config\n')
            target.write_text('user edited config\n')
            rice.apply_configs(selection, home, update=True, conflict='apply')
            self.assertEqual(target.read_text(), 'user edited config\n')
            pending = Path(str(target) + '.new')
            self.assertEqual(json.loads(pending.read_text())['logo']['source'], 'gentoo')
            pending.write_text('user edited review\n')
            rice.apply_configs(selection, home, update=True, conflict='apply')
            self.assertEqual(pending.read_text(), 'user edited review\n')

    def test_shortcut_launchers_expand_target_home(self):
        selection = rice.load_selection()
        selection['configs'] = ['kde-shortcuts']
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rice.apply_configs(selection, home, conflict='apply')
            desktop = home / '.local/share/applications/net.local.fiw-shot-region.desktop'
            self.assertIn('Exec="' + str(home) + '/.local/bin/fiw-shot" region', desktop.read_text())
            self.assertNotIn('{{HOME}}', desktop.read_text())
            self.assertTrue((home / '.local/bin/fiw-shot').stat().st_mode & 0o111)

    def test_actual_kde_session_is_rejected_before_any_writes(self):
        selection = rice.load_selection()
        selection['configs'] = ['kde-style']
        with tempfile.TemporaryDirectory() as temp, patch.object(rice, 'active_plasma', return_value=True):
            home = Path(temp)
            with self.assertRaises(RuntimeError):
                rice.apply_configs(selection, home, conflict='apply')
            self.assertEqual(list(home.iterdir()), [])

    def test_source_plan_distinguishes_binary_payloads_and_dependencies(self):
        output = '[binary N ] app-misc/jq-1.8.2::gentoo\n[ebuild N ] dev-libs/foo-2.0::gentoo\n[ebuild N ] games-util/ge-proton-bin-11.7::fiw-dots\n[ebuild N ] kde-misc/apdatifier-gentoo-1.0.0::fiw-dots\n'
        self.assertEqual(rice.source_builds(output), {'dev-libs/foo-2.0'})
        self.assertEqual(rice.cp_from_cpv('dev-libs/foo-2.0'), 'dev-libs/foo')

    def test_configs_restore_without_installing_package_sections(self):
        selection = rice.load_selection()
        selection['groups'] = []
        selection['configs'] = ['fish', 'kitty', 'neovim', 'fastfetch']
        selection['extras'] = []
        self.assertEqual(rice.package_map(selection), {})
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            report = rice.apply_configs(selection, home, conflict='apply')
            self.assertTrue(report['applied'])
            for relative in ['.config/fish/conf.d/fiw.fish', '.config/kitty/kitty.conf',
                             '.config/nvim/init.lua', '.config/fastfetch/config.jsonc']:
                self.assertTrue((home / relative).is_file(), relative)
        self.assertNotIn('inactive', rice.preview(selection))

    def test_category_separation_and_stock_kernel(self):
        selection = rice.load_selection()
        packages = rice.package_map(selection)
        self.assertIn('sys-kernel/gentoo-kernel-bin', packages['system'])
        self.assertNotIn('sys-kernel/gentoo-kernel', packages['system'])
        self.assertFalse(any(p.startswith('=sys-kernel/gentoo-kernel-') for p in packages['system']))
        self.assertNotIn('kde-apps/dolphin', packages['kde'])
        self.assertIn('kde-apps/dolphin', packages['fiw-apps'])
        self.assertNotIn('kde-apps/filelight', packages['fiw-apps'])
        self.assertEqual(selection['bootloader'], 'keep')
        self.assertNotIn('autostart', selection['configs'])


if __name__ == '__main__':
    unittest.main()
