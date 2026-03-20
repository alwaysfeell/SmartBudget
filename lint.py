#!/usr/bin/env python3
"""
SmartBudget Static Linter
PEP 8 + best practices checker using Python's built-in ast and tokenize.
"""

import ast
import tokenize
import io
import os
import sys
import re
from pathlib import Path

IGNORE_DIRS = {'__pycache__', '.git', 'venv', '.venv', 'templates'}
MAX_LINE_LENGTH = 100

issues = []

def report(filepath, line, col, code, message):
    issues.append((filepath, line, col, code, message))


# ─── PEP 8 checks via tokenize ────────────────────────────────────────────────

def check_style(filepath, source):
    lines = source.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.rstrip('\n')

        # E501 — line too long
        if len(stripped) > MAX_LINE_LENGTH:
            report(filepath, i, MAX_LINE_LENGTH + 1, 'E501',
                   f'Line too long ({len(stripped)} > {MAX_LINE_LENGTH} chars)')

        # W291 — trailing whitespace
        if stripped != stripped.rstrip():
            report(filepath, i, len(stripped.rstrip()) + 1, 'W291', 'Trailing whitespace')

        # W293 — whitespace before blank line
        if stripped.strip() == '' and stripped != '':
            report(filepath, i, 1, 'W293', 'Whitespace on blank line')

        # E711 — comparison to None
        if re.search(r'==\s*None|!=\s*None', stripped) and '==' in stripped:
            report(filepath, i, 1, 'E711', 'Comparison to None (use "is None" or "is not None")')

        # E712 — comparison to True/False
        if re.search(r'==\s*True|==\s*False|!=\s*True|!=\s*False', stripped):
            report(filepath, i, 1, 'E712', 'Comparison to True/False (use "if x:" or "if not x:")')


    # W391 — blank line at end of file
    if lines and lines[-1].strip() == '':
        report(filepath, len(lines), 1, 'W391', 'Blank line at end of file')

    # W292 — no newline at end of file
    if source and not source.endswith('\n'):
        report(filepath, len(lines), 1, 'W292', 'No newline at end of file')


# ─── AST checks ───────────────────────────────────────────────────────────────

def check_ast(filepath, source):
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        report(filepath, e.lineno or 1, 1, 'E999', f'SyntaxError: {e.msg}')
        return

    for node in ast.walk(tree):

        # F401 — unused imports (basic: checks if name appears in rest of file)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.asname or alias.name.split('.')[0] for alias in node.names]
            else:
                names = [alias.asname or alias.name for alias in node.names if alias.name != '*']
            for name in names:
                # Simple check: does the name appear at all in source besides import line?
                src_without_import = '\n'.join(
                    l for i, l in enumerate(source.splitlines(), 1) if i != node.lineno
                )
                if name not in src_without_import:
                    report(filepath, node.lineno, 1, 'F401', f"'{name}' imported but unused")

        # C901 — function complexity (count branches)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                      ast.With, ast.Assert, ast.comprehension)):
                    complexity += 1
                if isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
            if complexity > 10:
                report(filepath, node.lineno, 1, 'C901',
                       f"Function '{node.name}' has cyclomatic complexity {complexity} (> 10)")

        # E741 — ambiguous variable names
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign) and node.target:
                targets = [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id in ('l', 'O', 'I'):
                    report(filepath, node.lineno, 1, 'E741',
                           f"Ambiguous variable name '{t.id}'")

        # W0611 — bare except
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            report(filepath, node.lineno, 1, 'W0611', 'Bare except clause catches all exceptions')

        # missing docstrings (top-level public functions only)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.col_offset == 0:
                if not (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                    if not node.name.startswith('_'):
                        report(filepath, node.lineno, 1, 'D100',
                               f"Public function '{node.name}' missing docstring")

        # B006 — mutable default argument
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    report(filepath, node.lineno, 1, 'B006',
                           f"Mutable default argument in '{node.name}'")


# ─── Runner ───────────────────────────────────────────────────────────────────

def lint_file(filepath):
    with open(filepath, encoding='utf-8', errors='ignore') as f:
        source = f.read()
    check_style(filepath, source)
    check_ast(filepath, source)


def lint_project(root):
    root = Path(root)
    py_files = []
    for path in sorted(root.rglob('*.py')):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.name == 'lint.py':
            continue
        py_files.append(path)
    return py_files


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    files = lint_project(root)

    print(f"SmartBudget Linter — перевірка {len(files)} файлів\n{'=' * 60}")

    for f in files:
        lint_file(f)

    # Group by file
    by_file = {}
    for filepath, line, col, code, msg in issues:
        by_file.setdefault(filepath, []).append((line, col, code, msg))

    total = len(issues)
    file_count = len(by_file)

    for filepath, file_issues in sorted(by_file.items()):
        print(f"\n{filepath} ({len(file_issues)} issues):")
        for line, col, code, msg in sorted(file_issues):
            print(f"  {line:>4}:{col:<3} [{code}] {msg}")

    print(f"\n{'=' * 60}")
    print(f"Знайдено {total} проблем у {file_count} файлах з {len(files)} перевірених")

    # Summary by code
    from collections import Counter
    codes = Counter(code for _, _, _, code, _ in issues)
    print("\nРозподіл за типами:")
    for code, count in sorted(codes.items(), key=lambda x: -x[1]):
        print(f"  {code}: {count}")
