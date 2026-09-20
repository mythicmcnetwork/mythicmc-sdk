"""Regression checks for the gates that prevent incorrect registry releases."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for path in ('scripts/check-release.py', 'typescript/package.json',
                     'typescript/package-lock.json', 'typescript/src/client.ts',
                     'python/pyproject.toml', 'python/src/mythicmc/client.py', 'openapi.yaml'):
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / path, dest)
        shutil.copytree(ROOT / 'changelog', self.root / 'changelog')
        self.version = __import__('json').loads((self.root / 'typescript/package.json').read_text())['version']
        self.env = {key: value for key, value in os.environ.items() if not key.startswith('GITHUB_')}

    def tearDown(self):
        self.temp.cleanup()

    def run_check(self, **env):
        return subprocess.run([__import__('sys').executable, 'scripts/check-release.py'],
                              cwd=self.root, env={**self.env, **env}, capture_output=True, text=True)

    def test_manual_validation_does_not_require_a_new_tag(self):
        self.assertEqual(self.run_check(GITHUB_EVENT_NAME='workflow_dispatch').returncode, 0)

    def test_runtime_version_mismatch_stops_release(self):
        path = self.root / 'python/src/mythicmc/client.py'
        path.write_text(path.read_text().replace(f'__version__ = "{self.version}"', '__version__ = "9.9.9"'))
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('versions disagree', result.stderr)

    def test_missing_notes_stop_release(self):
        (self.root / f'changelog/{self.version}-changelog.md').unlink()
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_wrong_tag_stops_release(self):
        result = self.run_check(GITHUB_EVENT_NAME='push', GITHUB_REF='refs/tags/v9.9.9')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Tag must be', result.stderr)

    def test_tag_must_be_from_main(self):
        def git(*args):
            subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True)
        git('init', '-b', 'main')
        git('add', '.')
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'main')
        git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.assertEqual(self.run_check(GITHUB_EVENT_NAME='push', GITHUB_REF=f'refs/tags/v{self.version}').returncode, 0)
        git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'unmerged')
        self.assertNotEqual(self.run_check(GITHUB_EVENT_NAME='push', GITHUB_REF=f'refs/tags/v{self.version}').returncode, 0)


if __name__ == '__main__':
    unittest.main()
