"""NYVERRA Alpha 0.31: offline source/data validation (not an Unreal compilation)."""
from pathlib import Path
import csv, py_compile, json, sys, zipfile
root = Path(__file__).resolve().parents[1]
errors = []
checks = []
def check(condition, label):
    checks.append((label, bool(condition)))
    if not condition: errors.append(label)

up = root / 'NYVERRA.uproject'
check(up.is_file(), 'uproject exists')
if up.exists():
    p = json.loads(up.read_text(encoding='utf-8-sig'))
    check(any(m.get('Name') == 'NYVERRA' for m in p.get('Modules', [])), 'runtime module declared')
for required in ('Source/NYVERRA/Private/NyGameMode.cpp', 'Source/NYVERRA/Private/NyCharacter.cpp',
                 'Source/NYVERRA/Private/NyEnemy.cpp', 'Source/NYVERRA/Private/NyFoliageCluster.cpp',
                 'Source/NYVERRA/NYVERRA.Build.cs'):
    check((root / required).is_file(), required)
for file in sorted((root / 'Tools').glob('*.py')):
    try: py_compile.compile(str(file), doraise=True, cfile=str(file.with_suffix('.pyc')))
    except Exception as ex: errors.append(f'Python syntax: {file.name}: {ex}')
    finally: file.with_suffix('.pyc').unlink(missing_ok=True)
check('TActorIterator<APlayerStart>' in (root/'Source/NYVERRA/Private/NyGameMode.cpp').read_text(), 'authored spawn point guard')
check(not list((root/'Content').rglob('*.umap')), 'no packaged map: editor step still required')
print('NYVERRA ALPHA 0.31 OFFLINE CHECK')
for label, ok in checks: print(('PASS' if ok else 'FAIL'), label)
print('UNVERIFIED: Unreal Engine C++ compilation, editor scripts, PIE, network runtime')
print('EDITOR TODO: create or import level, configure navigation and save .umap')
if errors:
    print('ERRORS:', *errors, sep='\n  - ')
    sys.exit(1)
print('OFFLINE CHECKS PASSED (not a playable build)')
