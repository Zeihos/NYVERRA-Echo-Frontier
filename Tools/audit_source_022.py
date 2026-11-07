"""Offline checks: python Tools/audit_source_022.py (no Unreal installation required)."""
from pathlib import Path
import ast, json, sys
root=Path(__file__).resolve().parents[1]
issues=[]
for p in (root/'Tools').glob('*.py'):
    try: ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    except SyntaxError as exc: issues.append(f'{p.name}: {exc}')
try:
    project=json.loads((root/'NYVERRA.uproject').read_text())
    assert any(m.get('Name')=='NYVERRA' for m in project['Modules'])
except Exception as exc: issues.append(f'uproject: {exc}')
for name in ('NyCharacter','NyGameMode','NyEnemy','NyResource','NyWorldState'):
    for folder,suffix in [('Public','.h'),('Private','.cpp')]:
        path=root/'Source'/'NYVERRA'/folder/(name+suffix)
        if not path.exists():issues.append('Missing '+str(path))
height=root/'Content'/'TerrainSource'/'NyverraTestLandscape_505x505_R16.png'
if not height.is_file():issues.append('Missing heightmap')
print('NYVERRA source audit:', 'PASS' if not issues else 'FAIL')
for issue in issues: print(' -',issue)
print('WARNING: Does NOT compile UE C++, verify Editor Python API, or test gameplay.')
sys.exit(bool(issues))
