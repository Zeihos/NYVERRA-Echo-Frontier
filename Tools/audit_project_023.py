"""Offline structural audit, no Unreal installation required."""
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
errors=[]
checks=['NYVERRA.uproject','Source/NYVERRA/NYVERRA.Build.cs',
'Source/NYVERRA/Private/NyCharacter.cpp','Source/NYVERRA/Private/NyWorldState.cpp',
'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png',
'Tools/create_terrain_materials_023.py']
for rel in checks:
    if not (root/rel).is_file(): errors.append('missing '+rel)
config=(root/'Config/DefaultEngine.ini').read_text(encoding='utf-8')
if '/Game/Maps/TestWorld' in config:
    if not list((root/'Content/Maps').glob('TestWorld.umap')) if (root/'Content/Maps').exists() else True:
        errors.append('nonexistent TestWorld assigned as default map')
print('NYVERRA 0.23 offline audit:', 'FAIL' if errors else 'PASS')
for e in errors: print(' -',e)
sys.exit(bool(errors))
