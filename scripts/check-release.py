"""Reject mismatched release versions before any package can be published."""
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib

root = Path(__file__).resolve().parents[1]
package = json.loads((root / 'typescript/package.json').read_text())
version = package['version']
if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
    raise SystemExit('Only stable major.minor.patch releases are supported.')
lock = json.loads((root / 'typescript/package-lock.json').read_text())
python = tomllib.loads((root / 'python/pyproject.toml').read_text())
versions = {
    'TypeScript manifest': version,
    'lockfile': lock['version'],
    'lockfile root package': lock['packages']['']['version'],
    'Python manifest': python['project']['version'],
}
for label, path, pattern in [
    ('TypeScript runtime', 'typescript/src/client.ts', r"export const VERSION = '([^']+)'"),
    ('Python runtime', 'python/src/mythicmc/client.py', r'__version__ = "([^"]+)"'),
    ('OpenAPI', 'openapi.yaml', r'^  version: (\S+)$'),
]:
    match = re.search(pattern, (root / path).read_text(), re.MULTILINE)
    if not match:
        raise SystemExit(f'Cannot find version in {path}')
    versions[label] = match[1]
if any(value != version for value in versions.values()):
    raise SystemExit(f'Release versions disagree: {versions}')
notes = root / f'changelog/{version}-changelog.md'
if not notes.is_file() or not notes.read_text().strip():
    raise SystemExit(f'Missing changelog: {notes.relative_to(root)}')
if os.environ.get('GITHUB_EVENT_NAME') == 'push':
    if os.environ.get('GITHUB_REF') != f'refs/tags/v{version}':
        raise SystemExit(f'Tag must be v{version}, matching both SDKs.')
    subprocess.run(['git', 'merge-base', '--is-ancestor', 'HEAD', 'origin/main'], cwd=root, check=True)
if os.environ.get('GITHUB_OUTPUT'):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write(f'version={version}\n')
print(f'Release versions and changelog agree: {version}')
