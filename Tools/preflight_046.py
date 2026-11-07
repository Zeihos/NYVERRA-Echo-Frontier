from pathlib import Path
import json, re, sys, zipfile
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(label, ok, detail=''):
    checks.append((label,bool(ok),detail)); print(('PASS' if ok else 'FAIL')+' | '+label+(' | '+detail if detail else ''))
project=ROOT/'NYVERRA.uproject'
try:
    cfg=json.loads(project.read_text(encoding='utf-8-sig'))
except Exception as exc:
    cfg={}; check('uproject JSON',False,str(exc))
else:
    check('uproject JSON',True)
check('runtime module',any(m.get('Name')=='NYVERRA' for m in cfg.get('Modules',[])))
source=ROOT/'Source'/'NYVERRA'
check('module rules',(source/'NYVERRA.Build.cs').is_file())
for target in ('NYVERRA.Target.cs','NYVERRAEditor.Target.cs','NYVERRAServer.Target.cs'):
    check(target,(ROOT/'Source'/target).is_file())
headers=list((source/'Public').glob('*.h'))
cpp=list((source/'Private').glob('*.cpp'))
check('C++ headers and sources',len(headers)>=5 and len(cpp)>=5,f'{len(headers)} headers, {len(cpp)} cpp')
check('terrain heightmap',(ROOT/'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png').is_file())
check('saved .umap exists',bool(list((ROOT/'Content').rglob('*.umap'))),'A saved game map is still required for gameplay.')
check('Unreal build tool available here',False,'Run BUILD_ALPHA_046_WINDOWS.bat on Windows with UE 5.8 installed.')
failed=sum(not passed for _,passed,_ in checks)
print(f'\n{len(checks)-failed}/{len(checks)} checks passed. The two environment/map checks are expected until the UE editor is used.')
sys.exit(1 if any(not passed for name,passed,_ in checks if name not in ('saved .umap exists','Unreal build tool available here')) else 0)
