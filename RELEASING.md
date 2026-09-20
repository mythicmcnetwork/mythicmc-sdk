# Releasing the SDKs

Push a stable version tag such as `v1.2.0` to publish both SDKs. GitHub Actions validates the version, runs CI, builds the archives, publishes them to npm and PyPI, then creates the GitHub release with notes and checksums. Both registries authenticate the workflow through OIDC; no registry token is stored in GitHub.

## Prepare a release

1. Update the version in `typescript/package.json`, both root version entries in `typescript/package-lock.json`, `typescript/src/client.ts`, `python/pyproject.toml`, `python/src/mythicmc/client.py`, and `openapi.yaml`.
2. Add `changelog/<version>-changelog.md` with consumer-facing changes and migration instructions. Keep `RELEASE_NOTES.md` current.
3. Commit and push the changes to `main`. Wait for CI to pass.
4. Create and push the matching tag, for example:

   ```sh
   git tag -a v1.2.0 -m 'MythicMC SDK 1.2.0'
   git push origin v1.2.0
   ```

Only stable `major.minor.patch` versions are supported. The tag must match every version field, and its commit must be reachable from `main`. Existing published versions cannot be overwritten; use a new version for changes.

## Validate the automation without publishing

Run **Actions → Release SDKs → Run workflow**, selecting `main`, or:

```sh
gh workflow run release.yml --ref main
```

On `main`, this runs validation, tests and packaging. Publishing jobs are skipped because the `release` environment permits only version tags. It does not upload packages or create a GitHub release. The built archives remain available as the `sdk-release` workflow artifact.

Once a version tag contains this workflow, manually dispatching on that tag also checks trusted publisher authentication without uploading packages. Automatic publication occurs only on tag pushes.

## One-time registry configuration

Configure each existing package's GitHub trusted publisher with owner `mythicmcnetwork`, repository `mythicmc-sdk`, workflow filename `release.yml`, and environment `release`. npm must allow direct `npm publish`. The GitHub `release` environment allows only `v*` tags; no branch can access it.

## Failed releases

If one publishing job succeeds and the other fails, use **Re-run failed jobs** on the original tag run. Do not move the tag or rerun successful publishing jobs. The GitHub release is created only after both registry jobs succeed. Check the registry before retrying an upload with an uncertain result.
