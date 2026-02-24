#!/usr/bin/env python3
"""
Check that src/codegen does not depend on project_manager.

Exits with 0 if no file under src/codegen contains "project_manager".
Exits with 1 and prints offending files/lines otherwise.

Used to enforce the decoupling goal: codegen should depend on config,
design_data, and injected dependencies (e.g. LinkSink), not on project_manager.
"""

from pathlib import Path


def main() -> int:
    codegen_dir = Path(__file__).resolve().parent.parent / "src" / "codegen"
    if not codegen_dir.is_dir():
        print(f"Error: codegen dir not found: {codegen_dir}")
        return 2

    violations: list[tuple[Path, int, str]] = []
    for path in sorted(codegen_dir.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Error reading {path}: {e}")
            return 2
        for i, line in enumerate(text.splitlines(), start=1):
            if "project_manager" in line:
                violations.append((path, i, line.strip()))

    if not violations:
        return 0

    repo_root = codegen_dir.parent.parent
    print("project_manager must not appear in src/codegen. Violations:")
    for path, line_no, content in violations:
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            rel = path
        print(f"  {rel}:{line_no}: {content[:80]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
