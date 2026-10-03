import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('rice', Path(__file__).resolve().parents[1] / 'lib/rice.py')
rice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rice)


class ProposalTests(unittest.TestCase):
    def create(self, home):
        selection = rice.load_selection()
        selection.update(groups=[], configs=['fastfetch'])
        rice.apply_configs(selection, home, conflict='apply')
        target = home / '.config/fastfetch/config.jsonc'
        target.write_text('local preferences\n')
        rice.apply_configs(selection, home, update=True, conflict='apply')
        candidate = Path(str(target) + '.new')
        return selection, target, candidate, candidate.relative_to(home).as_posix()

    def test_accept_backs_up_local_file_and_keeps_other_proposals(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.proposals.os, 'geteuid', return_value=1000):
            home = Path(temp)
            selection, target, candidate, proposal_id = self.create(home)
            proposed = candidate.read_bytes()
            rice.apply_configs(selection, home, update=True, conflict='apply')
            pending = rice.proposals.list_proposals(home, rice.backup_paths())
            self.assertEqual(len(pending), 2)
            self.assertIn('-local preferences', rice.proposals.preview(home, proposal_id, rice.backup_paths()))
            report = rice.proposals.accept(home, proposal_id, rice.backup_paths(), lambda *args: 'apply', lambda *args: False)
            self.assertEqual(target.read_bytes(), proposed)
            backup = rice.backups.user_state(home) / 'backups' / report['backup'] / '.config/fastfetch/config.jsonc'
            self.assertEqual(backup.read_text(), 'local preferences\n')
            self.assertFalse(candidate.exists())
            pending = rice.proposals.list_proposals(home, rice.backup_paths())
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]['status'], 'unchanged')
            index = json.loads((rice.backups.user_state(home) / 'managed.json').read_text())
            self.assertEqual(index['.config/fastfetch/config.jsonc'], rice.digest(target))

    def test_keep_and_stale_targets_preserve_both_files(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.proposals.os, 'geteuid', return_value=1000):
            home = Path(temp)
            _, target, candidate, proposal_id = self.create(home)
            original_proposal = candidate.read_bytes()
            rice.proposals.accept(home, proposal_id, rice.backup_paths(), lambda *args: 'keep', lambda *args: False)
            self.assertEqual(target.read_text(), 'local preferences\n')
            self.assertEqual(candidate.read_bytes(), original_proposal)
            target.write_text('newer local preferences\n')
            with self.assertRaisesRegex(RuntimeError, 'changed since'):
                rice.proposals.accept(home, proposal_id, rice.backup_paths(), lambda *args: 'apply', lambda *args: False)
            self.assertEqual(target.read_text(), 'newer local preferences\n')
            self.assertEqual(candidate.read_bytes(), original_proposal)

    def test_target_change_during_confirmation_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.proposals.os, 'geteuid', return_value=1000):
            home = Path(temp)
            _, target, candidate, proposal_id = self.create(home)
            def confirm(*args):
                target.write_text('app rewrote its config\n')
                return 'apply'
            with self.assertRaisesRegex(RuntimeError, 'changed during'):
                rice.proposals.accept(home, proposal_id, rice.backup_paths(), confirm, lambda *args: False)
            self.assertEqual(target.read_text(), 'app rewrote its config\n')
            self.assertTrue(candidate.is_file())

    def test_manually_edited_proposal_remains_local_on_future_updates(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.proposals.os, 'geteuid', return_value=1000):
            home = Path(temp)
            selection, target, candidate, proposal_id = self.create(home)
            candidate.write_text('chosen custom config\n')
            rice.proposals.accept(home, proposal_id, rice.backup_paths(), lambda *args: 'apply', lambda *args: False)
            rice.apply_configs(selection, home, update=True, conflict='apply')
            self.assertEqual(target.read_text(), 'chosen custom config\n')
            self.assertTrue(candidate.is_file())

    def test_proposal_change_during_confirmation_requires_another_review(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.proposals.os, 'geteuid', return_value=1000):
            home = Path(temp)
            _, target, candidate, proposal_id = self.create(home)
            def confirm(*args):
                candidate.write_text('edited proposal during review\n')
                return 'apply'
            with self.assertRaisesRegex(RuntimeError, 'proposal changed during'):
                rice.proposals.accept(home, proposal_id, rice.backup_paths(), confirm, lambda *args: False)
            self.assertEqual(target.read_text(), 'local preferences\n')
            self.assertEqual(candidate.read_text(), 'edited proposal during review\n')

    def test_paths_outside_home_and_live_kde_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(rice.proposals.os, 'geteuid', return_value=1000):
            root = Path(temp); home = root / 'home'; home.mkdir()
            outside = root / 'outside'; outside.mkdir()
            _, target, candidate, proposal_id = self.create(home)
            config = home / '.config'
            config.rename(home / 'saved-config')
            config.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                rice.proposals.list_proposals(home, rice.backup_paths())
            config.unlink(); (home / 'saved-config').rename(config)
            allowed = rice.backup_paths()
            allowed['.config/fastfetch/config.jsonc']['kde'] = True
            with self.assertRaisesRegex(RuntimeError, 'Log out'):
                rice.proposals.accept(home, proposal_id, allowed, lambda *args: 'apply', lambda *args: True)
            self.assertEqual(target.read_text(), 'local preferences\n')
            self.assertTrue(candidate.is_file())

    def test_shared_kconfig_generates_one_complete_proposal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); home = root / 'home'; home.mkdir()
            relative = Path('.config/kwinrc')
            target = home / relative; target.parent.mkdir()
            target.write_text('[Appearance]\ncolour=orange\n[Desktops]\nNumber=4\n[Other]\nkeep=yes\n')
            style, shortcuts = root / 'style', root / 'shortcuts'
            style.write_text('[Appearance]\ncolour=purple\n')
            shortcuts.write_text('[Desktops]\nNumber=1\n')
            entries = [('kde-style', 'kconfig', style, relative), ('kde-shortcuts', 'kconfig', shortcuts, relative)]
            with patch.object(rice, 'config_entries', return_value=entries):
                rice.apply_configs(rice.load_selection(), home, update=True, conflict='apply')
            choices = rice.proposals.list_proposals(home, rice.backup_paths())
            self.assertEqual(len(choices), 1)
            content = (home / choices[0]['id']).read_text()
            for value in ('colour=purple', 'Number=1', 'keep=yes'):
                self.assertIn(value, content)
            self.assertIn('colour=orange', target.read_text())


if __name__ == '__main__':
    unittest.main()
