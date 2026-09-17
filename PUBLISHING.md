# Publishing the monitoring SDKs

## JavaScript / npm

| Package | Directory | Published version |
| --- | --- | --- |
| `@prilog/monitoring` | `node/` | `0.1.0` |
| `@prilog/monitoring-browser` | `browser/` | `0.1.0` |

Both packages publish publicly to `https://registry.npmjs.org/`. Each package includes its public entry point, obfuscated runtime implementation, package metadata, README, and MIT license.

## Authenticate

Use an npm account with publish access to the `@prilog` scope and two-factor authentication enabled:

```bash
npm login --registry=https://registry.npmjs.org/
npm whoami --registry=https://registry.npmjs.org/
```

Complete npm's browser approval when publishing. If npm reports `EOTP` in a noninteractive session, run the publish command in an interactive terminal to approve it directly. A successful login alone does not satisfy publication approval.

## Prepare a release

Increment the package version in `package.json` and `package-lock.json`, and update the matching `prilog.sdk.version` attribute in the separately maintained readable sources. The Node SDK's logger version should also match its package version. Update documentation for the release. Published versions are immutable; the original npm `0.1.0` releases contain readable code and cannot be overwritten with these obfuscated builds.

Regenerate the runtime artifacts from the repository root, following [BUILDING.md](BUILDING.md):

```bash
npm ci
npm run build -- /path/to/readable-sdk
npm run build -- /path/to/readable-sdk --check
```

From `node/`:

```bash
npm ci
npm test
npm pack --dry-run
```

From `browser/`:

```bash
npm ci
npx playwright install chromium --only-shell
npm test
npm pack --dry-run
```

## Publish

Run from the directory of the package being released:

```bash
npm publish --access public --registry=https://registry.npmjs.org/
```

The `prepublishOnly` hook runs the package's integration tests against the generated runtime before upload. Consumers bundle the browser SDK in their application.

## Verify

Check the latest public versions:

```bash
npm view @prilog/monitoring version --registry=https://registry.npmjs.org/
npm view @prilog/monitoring-browser version --registry=https://registry.npmjs.org/
```

Install the released versions in a separate project and confirm that their exported APIs load successfully.

## Python / PyPI

The project name is `prilog-monitoring`. Build from the generated, obfuscated runtime after following `BUILDING.md`:

```bash
python -m pip install build twine
python -m build python
python -m twine check python/dist/*
```

Authenticate with a PyPI API token or configured trusted publisher. A token can be stored locally with keyring:

```bash
python -m keyring set https://upload.pypi.org/legacy/ __token__
```

Enter the token at the hidden prompt. Then publish and verify:

```bash
python -m twine upload --non-interactive python/dist/*
python -m pip install --index-url https://pypi.org/simple prilog-monitoring==0.1.0
```

Inspect both distribution archives before upload: they should contain the public Python facade and generated `_runtime.py`, along with metadata, documentation, and the license. Readable source inputs and build tools are maintained outside the distribution.

## Go module

The module path is `github.com/Prilog-ai/prilog-monitoring/golang`. Its releases use subdirectory tags, starting with `golang/v0.1.0`. Public module downloads require anonymous read access to this GitHub repository.

Run from `golang/`:

```bash
go test -race ./...
go vet ./...
```

Commit the generated SDK, metadata, tests, and documentation. From the repository root, publish the release tag after pushing the commit:

```bash
git tag golang/v0.1.0
git push origin golang/v0.1.0
```

Verify through the public module proxy and checksum database:

```bash
GOPROXY=https://proxy.golang.org GOSUMDB=sum.golang.org go mod download -json github.com/Prilog-ai/prilog-monitoring/golang@v0.1.0
```

Use a new semantic version tag for later Go releases. Published module versions and their checksums are immutable.
