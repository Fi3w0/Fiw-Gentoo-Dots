import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


launcher = module('launcher', REPO / 'lib/launcher.py')
audit = module('audit', REPO / 'tools/audit-packages.py')


class ReleaseTests(unittest.TestCase):
    def bundle(self, repo):
        for name in ('go.mod', 'go.sum', 'VERSION'):
            (repo / name).write_text('fixture')
        root = repo / 'assets/bin'; root.mkdir(parents=True)
        data = b'fixture-binary'
        archive = gzip.compress(data, mtime=0)
        (root / 'fiw-dots.gz').write_bytes(archive)
        metadata = {'source_sha256': launcher.source_hash(repo), 'binaries': {
            'linux-amd64': {'file': 'fiw-dots.gz', 'size': len(data),
                           'sha256': launcher.digest(data), 'gzip_sha256': launcher.digest(archive)}}}
        (root / 'tui.json').write_text(json.dumps(metadata))
        return data

    def test_bundle_runs_without_go_and_replaces_a_damaged_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp); data = self.bundle(repo)
            cache = repo / 'build/fiw-dots'; cache.parent.mkdir(); cache.write_bytes(b'damaged')
            with patch.object(launcher.platform, 'system', return_value='Linux'), patch.object(launcher.platform, 'machine', return_value='x86_64'), patch.object(launcher.shutil, 'which', return_value=None), patch.object(launcher.os, 'chdir'), patch.dict(launcher.os.environ, {'FIW_DOTS_SOURCE': '0'}), patch.object(launcher.subprocess, 'run') as run:
                self.assertEqual(launcher.launch(repo), cache)
                self.assertEqual(cache.read_bytes(), data)
                self.assertTrue(cache.stat().st_mode & 0o111)
                run.assert_not_called()

    def test_changed_frontend_and_modified_archives_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp); self.bundle(repo)
            cache = repo / 'build/fiw-dots'
            with patch.object(launcher.platform, 'system', return_value='Linux'), patch.object(launcher.platform, 'machine', return_value='x86_64'):
                archive = repo / 'assets/bin/fiw-dots.gz'
                original = archive.read_bytes(); archive.write_bytes(original + b'modified')
                with self.assertRaises(RuntimeError):
                    launcher.bundled(repo, cache)
                archive.write_bytes(original)
                (repo / 'cmd/dots').mkdir(parents=True)
                (repo / 'cmd/dots/main.go').write_text('changed frontend')
                with self.assertRaises(RuntimeError):
                    launcher.bundled(repo, cache)
            self.assertFalse(cache.exists())

    def test_audit_expands_only_selected_sets_and_preserves_java_slots(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); sets = root / 'sets'; sets.mkdir()
            world, selected = root / 'world', root / 'world_sets'
            world.write_text('=app-editors/vscode-1.0::old\n')
            selected.write_text('@desktop\n')
            (sets / 'desktop').write_text('app-editors/vscode\n@java\n')
            (sets / 'java').write_text('dev-java/openjdk-bin:21\n')
            (sets / 'not-selected').write_text('dev-libs/dependency-only\n')
            result, unresolved = audit.explicit(world, selected, sets)
            self.assertEqual(set(result), {'app-editors/vscode', 'dev-java/openjdk-bin:21'})
            self.assertEqual(unresolved, [])
            (sets / 'java').write_text('@desktop\n')
            with self.assertRaises(ValueError):
                audit.explicit(world, selected, sets)


if __name__ == '__main__':
    unittest.main()
