"""Offline structural checks; not an Unreal C++ build."""
from pathlib import Path
from PIL import Image
import ast
p=Path(__file__).resolve().parents[1]
for name in ('Soil','Grass','Rock'):
    f=p/'Content'/'TerrainSource'/'Textures'/f'T_Ny{name}_Albedo.png'
    im=Image.open(f)
    assert im.mode=='RGB' and im.size==(512,512),f
for f in (p/'Tools').glob('*.py'):
    ast.parse(f.read_text(encoding='utf-8'),str(f))
for f in ('NYVERRA.uproject','Source/NYVERRA/NYVERRA.Build.cs','Source/NYVERRA/Private/NyCharacter.cpp'):
    assert (p/f).is_file(),f
assert 'M_NyLandscape_Textured' in (p/'Tools'/'create_textured_landscape_025.py').read_text()
print('Alpha 0.25 offline checks: PASS (not an Unreal Editor / compiler validation)')
