"""Summarize an UnrealBuildTool log (Windows, no external dependencies)."""
from pathlib import Path
import re
import sys

PATTERNS = [
    re.compile(r'\berror\s+(?:C\d{4}|LNK\d{4}|MSB\d{4}|CS\d{4})\b', re.I),
    re.compile(r'\bfatal error\b', re.I),
    re.compile(r'\berror:\s', re.I),
    re.compile(r'\b(?:UnrealBuildTool|BuildException|AutomationException):.*(?:error|failed)', re.I),
    re.compile(r'^\s*ERROR\s*:', re.I),
]

def summarize(content):
    lines = content.splitlines()
    found = []
    seen = set()
    for number, line in enumerate(lines, 1):
        line = line.strip()
        if any(pattern.search(line) for pattern in PATTERNS) and line not in seen:
            seen.add(line)
            found.append(f'{number}: {line}')
    if not found:
        return 'No compiler error lines matched the filters. Check the full log for the actual failure.\n'
    return '\n'.join(found) + '\n'

def main():
    if len(sys.argv) != 3:
        print('Usage: py -3 Tools\\summarize_build_051.py LOG OUTPUT')
        return 2
    log = Path(sys.argv[1])
    if not log.is_file():
        print(f'Missing log: {log}')
        return 3
    content = log.read_text(encoding='utf-8-sig', errors='replace')
    output = Path(sys.argv[2])
    output.write_text(summarize(content), encoding='utf-8')
    print(f'Wrote {output}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
