"""Generate the portable Python runtime without distributing readable sources."""

import argparse
import ast
from pathlib import Path

import python_minifier


PUBLIC_NAMES = ["Monitoring", "capture_exception", "configuration", "init", "instrument_asyncio", "span"]
ROOT = Path(__file__).resolve().parent.parent


class EncodeStrings(ast.NodeTransformer):
    def __init__(self):
        self.values = []
        self.indexes = {}

    def visit_Constant(self, node):
        if not isinstance(node.value, str) or not node.value:
            return node
        if node.value not in self.indexes:
            self.indexes[node.value] = len(self.values)
            self.values.append(node.value)
        return ast.copy_location(
            ast.Subscript(value=ast.Name(id="_prilog_strings", ctx=ast.Load()),
                          slice=ast.Constant(self.indexes[node.value]), ctx=ast.Load()),
            node,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if source_root == ROOT or ROOT in source_root.parents:
        parser.error("Readable SDK sources must be outside this distribution repository.")
    source = (source_root / "python/prilog_monitoring/__init__.py").read_text()
    tree = ast.parse(source)
    # Public keyword arguments are part of the Python API.
    argument_names = {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)

    encoder = EncodeStrings()
    tree = encoder.visit(tree)
    encoded = ",".join(repr(value.encode("utf-8").hex()) for value in encoder.values)
    table = ast.parse(f"_prilog_strings=tuple(bytes.fromhex(value).decode('utf-8') for value in ({encoded},))").body[0]
    index = 0
    while index < len(tree.body) and isinstance(tree.body[index], (ast.Import, ast.ImportFrom)):
        index += 1
    tree.body.insert(index, table)
    ast.fix_missing_locations(tree)
    output = python_minifier.minify(
        ast.unparse(tree),
        rename_globals=True,
        rename_locals=True,
        preserve_globals=PUBLIC_NAMES,
        preserve_locals=sorted(argument_names),
        remove_literal_statements=True,
    )
    ast.parse(output, feature_version=(3, 9))
    compile(output, "_runtime.py", "exec")
    output = "# Copyright (c) 2026 Prilog. MIT. Generated runtime; see LICENSE.\n" + output + "\n"
    destination = ROOT / "python/prilog_monitoring/_runtime.py"
    if args.check:
        if destination.read_text() != output:
            raise SystemExit("Python runtime differs from the reproducible build.")
        print("Verified python/prilog_monitoring/_runtime.py")
    else:
        destination.write_text(output)
        print("Generated python/prilog_monitoring/_runtime.py")


if __name__ == "__main__":
    main()
