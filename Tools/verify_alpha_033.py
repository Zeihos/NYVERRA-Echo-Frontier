"""Offline structural checks. Does NOT compile or run Unreal Engine."""
from pathlib import Path
import json, zipfile, sys
root=Path(__file__).resolve().parents[1]
checks={
    'uproject':(root/'NYVERRA.uproject').exists(),
    'build_rules':(root/'Source/NYVERRA/NYVERRA.Build.cs').exists(),
    'game_mode':(root/'Source/NYVERRA/Private/NyGameMode.cpp').exists(),
    'character':(root/'Source/NYVERRA/Private/NyCharacter.cpp').exists(),
    'heightmap':(root/'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png').exists(),
    'respawn_ground_trace':'NyRespawnGround' in (root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(),
}
try:
    data=json.loads((root/'NYVERRA.uproject').read_text())
    checks['module_name']=any(x.get('Name')=='NYVERRA' for x in data.get('Modules',[]))
except Exception: checks['module_name']=False
for name,ok in checks.items():print(('PASS' if ok else 'FAIL')+' '+name)
print('NOTE: .umap must be saved in Unreal Editor; C++ must be compiled on Windows with UE5.')
sys.exit(0 if all(checks.values()) else 1)
