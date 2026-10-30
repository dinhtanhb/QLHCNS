"""Check the mobile KPI copy limit without importing Django or accessing a DB."""
import argparse
import ast
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def check_limits(root=ROOT):
    """Return matching limits, failing closed if either source cannot be read."""
    home = (root/'mobile/src/app/(tabs)/index.tsx').read_text(encoding='utf-8-sig')
    matches = re.findall(r'^\s*const\s+RECENT_KPI_LIMIT\s*=\s*(\d+)\s*;', home, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError('Expected one numeric RECENT_KPI_LIMIT declaration in Home')
    frontend = int(matches[0])
    tree = ast.parse((root/'src/apps/mobile/views.py').read_text(encoding='utf-8-sig'))
    pages = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'page']
    if len(pages) != 1:
        raise ValueError('Expected one page() function in mobile views')
    calls = [node for node in ast.walk(pages[0]) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == 'Paginator']
    if len(calls) != 1 or len(calls[0].args) < 2:
        raise ValueError('Expected one Paginator(queryset, limit) in page()')
    size = calls[0].args[1]
    if not isinstance(size, ast.Constant) or type(size.value) is not int:
        raise ValueError('page() size is no longer a numeric literal; update this check explicitly')
    backend = size.value
    if frontend < 1 or backend < 1 or frontend != backend:
        raise ValueError(f'KPI page limit mismatch: RECENT_KPI_LIMIT={frontend}, page() Paginator={backend}')
    return frontend, backend


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Repository root, defaults to this checkout')
    args = parser.parse_args()
    try:
        frontend, backend = check_limits(args.root.resolve())
    except (OSError, UnicodeError, SyntaxError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f'KPI page limit OK: frontend={frontend}, backend={backend}; no Django/DB access')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
