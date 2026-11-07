"""Static source checks only. Run with Python 3 outside UE."""
from pathlib import Path
import zipfile
root=Path(__file__).resolve().parents[1]
required=[root/'NYVERRA.uproject',root/'Source/NYVERRA/NYVERRA.Build.cs',root/'Source/NYVERRA/Private/NyCharacter.cpp',root/'Source/NYVERRA/Private/NyGameMode.cpp',root/'BUILD_ALPHA_036_WINDOWS.bat']
for f in required:
    assert f.is_file(),f'Missing: {f}'
s=(root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
assert 'Controller->GetPlayerViewPoint' not in s, 'Unsafe/nonportable controller viewpoint call remains'
assert s.count('GetPawnViewLocation()')>=2
assert s.count('GetControlRotation()')>=2
assert 'bSprinting&&!bIsDead&&Health>0.f&&Stamina>5.f' in s
print('PASS: Alpha 0.36 static source checks. Unreal C++ compilation NOT performed.')
