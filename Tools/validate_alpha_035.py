"""Offline preflight; does NOT claim to compile or test Unreal gameplay."""
import ast
from pathlib import Path
import json
import sys
root = Path(__file__).resolve().parents[1]
errors=[]
for rel in ['NYVERRA.uproject','Config/DefaultEngine.ini','Source/NYVERRA/NYVERRA.Build.cs',
            'Source/NYVERRA/Private/NyGameMode.cpp','Source/NYVERRA/Private/NyCharacter.cpp',
            'Tools/create_test_world.py','Tools/set_test_world_default.py']:
    if not (root/rel).is_file():errors.append('Missing '+rel)
for p in (root/'Tools').rglob('*.py'):
    try: ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
    except (SyntaxError,UnicodeError) as exc:errors.append(str(exc))
try:
    cfg=json.loads((root/'NYVERRA.uproject').read_text(encoding='utf-8-sig'))
    if not any(x.get('Name')=='NYVERRA' for x in cfg.get('Modules',[])):
        errors.append('Missing NYVERRA runtime module')
except (OSError,ValueError) as exc:errors.append(str(exc))
ini=(root/'Config/DefaultEngine.ini').read_text(encoding='utf-8-sig') if (root/'Config/DefaultEngine.ini').exists() else ''
if '/Game/Maps/TestWorld' in ini and not (root/'Content/Maps/TestWorld.umap').exists():
    errors.append('Default map TestWorld assigned but .umap is missing')
print('NYVERRA Alpha 0.35 offline validation:')
for error in errors: print('ERROR:',error)
print('Status:', 'FAIL' if errors else 'PASS (files and Python only; UE C++ not compiled)')
sys.exit(bool(errors))
