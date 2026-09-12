# Building the obfuscated SDKs

This repository distributes generated runtime implementations in `node/runtime.cjs` and `browser/runtime.js`. The small `index` entry points expose the public API with static CommonJS/ES module exports so consumers and bundlers can resolve them normally.

## Readable sources

Maintain the readable source directory separately, outside this repository, with this layout:

```text
readable-sdk/
  node/index.cjs
  browser/index.js
```

The build reads these files as inputs. It writes only the obfuscated runtimes and public entry points into this repository.

## Generate

Run from the repository root:

```bash
npm ci
npm run build -- /path/to/readable-sdk
```

The tool version and dependencies are locked. The fixed seed, renamed internal identifiers, encoded/rotated string arrays, and compact output produce reproducible builds. Source maps are disabled. Public API names, configuration property names, and static dependency imports are preserved. Browser output uses the `browser-no-eval` target, and the obfuscator's console suppression, anti-debugging, and self-defending transformations are disabled for application compatibility.

To verify that the checked-in artifacts match the same source inputs:

```bash
npm run build -- /path/to/readable-sdk --check
```

## Verify the distribution

Run the integration tests in both `node/` and `browser/` as described in the root README. Those tests load the generated runtime through the public entry points and exercise real OTLP export. Inspect each package with `npm pack --dry-run`; it should include its entry point, obfuscated runtime, package metadata, README, and LICENSE.

## Release versions

The previously published npm `0.1.0` packages contain the earlier readable implementation. Rewriting Git history cannot replace those npm artifacts. Increment the package and SDK runtime versions before publishing the obfuscated distribution as a new npm release.
