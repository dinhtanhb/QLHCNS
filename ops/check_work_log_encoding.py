"""Reject damaged work log headings and invalid UTF-8 before committing."""
from pathlib import Path


def main():
    path = Path(__file__).resolve().parents[1]/'docs/PROJECT_WORK_LOG.md'
    raw = path.read_bytes()
    text = raw.decode('utf-8', errors='strict')
    headings = [(number, line) for number, line in enumerate(text.splitlines(), 1) if line.startswith('#')]
    invalid = [number for number, line in headings if '?' in line]
    h1 = [line for _, line in headings if line.startswith('# ')]
    assert '\ufffd' not in text, 'Work log contains U+FFFD'
    assert not invalid, f'Question marks in headings: lines {invalid}'
    assert h1 == ['# Nhật ký công việc IHRMS'], f'Expected exactly one canonical H1; found {len(h1)}'
    print('UTF-8 OK; no U+FFFD or damaged headings; exactly one H1')


if __name__ == '__main__':
    main()
