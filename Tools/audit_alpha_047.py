"""Offline preflight only. Does not compile C++ or validate Unreal Editor APIs."""
from pathlib import Path
import csv, json, sys, zipfile
root=Path(__file__).resolve().parents[1]
errors=[]; warnings=[]
def check(condition,message):
    if not condition: errors.append(message)
project=root/'NYVERRA.uproject'
check(project.is_file(),'NYVERRA.uproject missing')
if project.exists():
    try:
        data=json.loads(project.read_text(encoding='utf-8-sig'))
        check(any(x.get('Name')=='NYVERRA' for x in data.get('Modules',[])),'NYVERRA module declaration missing')
    except (ValueError,UnicodeError) as e:errors.append('Project JSON invalid: '+str(e))
for name in ['NYVERRA.Build.cs','Private/NyGameMode.cpp','Private/NyCharacter.cpp','Private/NyEnemy.cpp','Private/NyFoliageCluster.cpp','Public/NyCharacter.h']:
    check((root/'Source/NYVERRA'/name).is_file(),'Missing Source/NYVERRA/'+name)
check((root/'Source/NYVERRAEditor.Target.cs').is_file(),'Editor target missing')
check((root/'Source/NYVERRAServer.Target.cs').is_file(),'Server target missing')
check((root/'Config/DefaultEngine.ini').is_file(),'Engine config missing')
# Source image is not an imported Landscape/level asset.
levels=list((root/'Content').rglob('*.umap')) if (root/'Content').exists() else []
if not levels: warnings.append('No saved .umap level: a playable terrain/map must be created inside Unreal Editor.')
if not list((root/'Content').rglob('*505x505*')): warnings.append('Could not locate 505x505 heightmap by filename.')
if not (root/'BUILD_ALPHA_047.log').exists():warnings.append('Unreal compile has not been run with BUILD_ALPHA_047_WINDOWS.bat in this folder.')
print('NYVERRA Alpha 0.47 offline audit')
for x in errors:print('ERROR:',x)
for x in warnings:print('WARNING:',x)
print('RESULT:', 'FAIL' if errors else 'PASS (offline structure only)')
sys.exit(1 if errors else 0)
