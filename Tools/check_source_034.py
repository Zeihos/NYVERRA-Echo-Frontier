"""Offline preflight: filesystem consistency only, not Unreal compilation."""
from pathlib import Path
from zipfile import ZipFile
import ast
import csv
import sys
root = Path(__file__).resolve().parents[1]
required = ['NYVERRA.uproject', 'Source/NYVERRA/NYVERRA.Build.cs', 'Source/NYVERRA/Private/NyGameMode.cpp', 'Source/NYVERRA/Private/NyEnemy.cpp', 'Tools/create_test_world.py', 'Tools/validate_runtime_map_034.py']
errors = []
for name in required:
    if not (root / name).is_file(): errors.append('Missing: '+name)
for p in (root/'Tools').glob('*.py'):
    try: ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    except (SyntaxError, UnicodeDecodeError) as e: errors.append(f'Python parse error in {p.name}: {e}')
if not (root/'Content'/'Maps'/'TestWorld.umap').is_file():
    print('NOTE: TestWorld.umap is not shipped. Generate it inside Unreal Editor after compiling.')
print('Python scripts found:',len(list((root/'Tools').glob('*.py'))))
print('C++ implementation files:',len(list((root/'Source').rglob('*.cpp'))))
for e in errors: print('ERROR:',e)
print('PASS filesystem preflight' if not errors else 'FAIL filesystem preflight')
sys.exit(bool(errors))
