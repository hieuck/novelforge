"""Tests that the engine boots correctly (regression: Unicode stdout fix)."""
from __future__ import annotations


def test_create_app_imports_and_runs(client):
    """Engine boots without errors (regression: Windows Unicode stdout)."""
    # If we got here, the fixture already called create_app() successfully
    assert True


def test_migrate_no_unicode_arrows():
    """migrate.py print statements should not contain Unicode arrows (Windows compat)."""
    import ast
    import sys

    with open("scripts/migrate.py", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if "\u2192" in arg.value or "\u2713" in arg.value:
                        print(
                            f"Found Unicode arrow in print at line {node.lineno}",
                            file=sys.stderr,
                        )
                        assert False, (
                            f"migrate.py line {node.lineno}: "
                            f"print() contains Unicode arrow '→' or '✓'. "
                            f"Use ASCII (e.g. '->' or '[OK]') for Windows cp1252 compat."
                        )

    assert True  # No Unicode arrows found
