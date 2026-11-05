"""Only the builder may import redstring (docs/adr/0001, point 2).

Every other module works on WFM-owned types, so the model, losses, curriculum
and loop are testable without a store. This test parses each module under
src/redstring_wfm and fails on a redstring import outside the allowed set.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "redstring_wfm"
ALLOWED_TO_IMPORT_REDSTRING = {"build.py"}


def _redstring_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        found.extend(n for n in names if n.split(".")[0] == "redstring")
    return found


def test_only_the_builder_imports_redstring() -> None:
    modules = sorted(PACKAGE.rglob("*.py"))
    # Guard against a vacuous pass if the path is wrong or the layout moves.
    assert modules, f"no modules found under {PACKAGE}"

    offenders = {
        str(path.relative_to(PACKAGE)): imports
        for path in modules
        if path.name not in ALLOWED_TO_IMPORT_REDSTRING and (imports := _redstring_imports(path))
    }
    assert offenders == {}, f"redstring imported outside the builder: {offenders}"
