# Building the obfuscated SDKs

This repository distributes generated runtime implementations for JavaScript, Python, and Go. JavaScript and Python have small public entry points; the Go module preserves exported types, fields, and methods while distributing obfuscated, buildable source.

## Readable sources

Maintain the readable source directory separately, outside this repository, with this layout:

```text
readable-sdk/
  node/index.cjs
  browser/index.js
  python/prilog_monitoring/__init__.py
  golang/prilog.go
```

The build reads these files as inputs. It writes only the obfuscated runtimes and public entry points into this repository.

## Generate JavaScript

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

## Generate Python

Using Python 3.14 and a virtual environment, run from the repository root:

```bash
python -m pip install -r scripts/python-build-requirements.txt
python scripts/obfuscate_python.py /path/to/readable-sdk
python scripts/obfuscate_python.py /path/to/readable-sdk --check
```

The pinned minifier renames internal bindings and compacts the runtime. Runtime string literals are encoded in a table. Public function names, attributes, and keyword arguments retain their API. The output is checked against Python 3.9 syntax and is packaged as portable Python code, without an interpreter-specific bytecode dependency. Use the same Python/minifier versions for byte-for-byte build checks.

Only `python/prilog_monitoring/_runtime.py` is generated. The public `__init__.py` exports the documented API. Both the wheel and source distribution contain this obfuscated runtime.

## Generate Go

The build tool requires Go 1.26; the distributed SDK requires Go 1.25. From the repository root:

```bash
go -C tools/go-obfuscate run . -source /path/to/readable-sdk/golang/prilog.go -module ../../golang
go -C tools/go-obfuscate run . -source /path/to/readable-sdk/golang/prilog.go -module ../../golang -check
```

The tool type-checks the readable input through a compiler overlay, renames implementation bindings using Go's symbol information, and encodes runtime strings. Imports, formatting directives, and the exported API retain the syntax needed by the compiler and tooling. The original source is never copied into the distribution tree.

The generated `golang/prilog.go` remains buildable with the standard Go compiler. Run `go test -race ./...` and `go vet ./...` in `golang/` before releasing it.

## Release versions

The previously published npm `0.1.0` packages contain the earlier readable implementation. Rewriting Git history cannot replace those npm artifacts. Increment the package and SDK runtime versions before publishing the obfuscated distribution as a new npm release.
