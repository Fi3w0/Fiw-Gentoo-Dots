import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ci_mirror', REPO / 'tools/ci/mirror.py')
ci_mirror = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci_mirror)


def git(*args):
    return subprocess.check_output(['git', *map(str, args)], text=True, stderr=subprocess.DEVNULL).strip()


def identity(path):
    for key, value in [('user.name', 'CI fixture'), ('user.email', 'ci-fixture'),
                       ('commit.gpgsign', 'false'), ('tag.gpgsign', 'false')]:
        git('-C', path, 'config', key, value)


class MirrorTests(unittest.TestCase):
    def test_mirror_preserves_tags_and_refs_and_refuses_divergence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); work, source, target = root / 'work', root / 'source.git', root / 'target.git'
            git('init', '-b', 'main', work); identity(work)
            (work / 'README').write_text('first\n')
            git('-C', work, 'add', 'README'); git('-C', work, 'commit', '-m', 'first')
            git('-C', work, 'branch', 'other'); git('-C', work, 'tag', '-a', 'v1', '-m', 'version1')
            git('clone', '--bare', work, source); git('init', '--bare', target)
            head = git('-C', work, 'rev-parse', 'HEAD')
            ci_mirror.mirror(str(source), str(target), source_ref='refs/tags/v1', source_sha=head)
            self.assertEqual(git('-C', source, 'show-ref'), git('-C', target, 'show-ref'))
            git('-C', target, 'branch', 'github-only', head)
            (work / 'README').write_text('source update\n')
            git('-C', work, 'commit', '-am', 'source update'); git('-C', work, 'push', source, 'main')
            diverged = root / 'diverged'
            git('clone', '--branch', 'main', target, diverged); identity(diverged)
            (diverged / 'other').write_text('GitHub edit\n')
            git('-C', diverged, 'add', 'other'); git('-C', diverged, 'commit', '-m', 'GitHub edit')
            git('-C', diverged, 'push', 'origin', 'main')
            before = git('-C', target, 'show-ref')
            ci_mirror.mirror(str(source), str(target), source_ref='refs/heads/main', source_sha=head)
            self.assertEqual(before, git('-C', target, 'show-ref'))
            with self.assertRaises(subprocess.CalledProcessError):
                ci_mirror.mirror(str(source), str(target))
            self.assertEqual(before, git('-C', target, 'show-ref'))


if __name__ == '__main__':
    unittest.main()
