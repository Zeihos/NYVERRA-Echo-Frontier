"""Offline sanity checks for NYVERRA Alpha 0.30. Does not compile Unreal C++."""
from pathlib import Path
from collections import Counter
import csv, json, struct, sys, zipfile
ROOT = Path(__file__).resolve().parents[1]
errors=[]; warnings=[]
def require(condition, message):
    if not condition: errors.append(message)

def checked(path):
    p=ROOT/path
    require(p.is_file(), f'Missing {path}')
    return p
project=checked('NYVERRA.uproject')
if project.is_file():
    data=json.loads(project.read_text(encoding='utf-8-sig'))
    require(data.get('Modules', [{}])[0].get('Name') == 'NYVERRA', 'Unreal module mismatch')
    print('EngineAssociation:',data.get('EngineAssociation'))
for p in ['Source/NYVERRA/NYVERRA.Build.cs','Source/NYVERRA/Private/NyGameMode.cpp',
          'Source/NYVERRA/Private/NyFoliageCluster.cpp','Tools/place_foliage_hism_029.py',
          'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png']:
    checked(p)
for path in ROOT.rglob('*.py'):
    compile(path.read_bytes(),str(path),'exec')
source=ROOT/'Source/NYVERRA/Private/NyFoliageCluster.cpp'
if source.is_file():
    txt=source.read_text(encoding='utf-8-sig')
    require('AddInstance(WorldTransform, true)' in txt,'HISM should place world-space transforms')
    require('bReplicates = false' in txt,'Foliage proxies must remain non-networked')
csvs=list((ROOT/'Content/TerrainSource').rglob('*FoliagePlacements.csv'))
require(bool(csvs),'Foliage placement CSV missing')
if csvs:
    with csvs[0].open(newline='',encoding='utf-8-sig') as fh:
        records=list(csv.DictReader(fh))
    counts=Counter(r['Kind'] for r in records)
    require(counts == {'Tree':240,'Rock':110,'Shrub':190},f'Foliage counts: {counts}')
    for i,r in enumerate(records):
        try:
            x,y,z=(float(r[k]) for k in ('X_cm','Y_cm','Z_cm'))
            if not all(abs(t)<1000000 for t in (x,y,z)):
                errors.append(f'Foliage out of bounds, row {i}')
        except (ValueError,KeyError): errors.append(f'Foliage invalid transform, row {i}')
png=ROOT/'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png'
if png.is_file():
    b=png.read_bytes()
    require(b[:8] == b'\x89PNG\r\n\x1a\n','Heightmap is not PNG')
    if len(b)>=29:
        w,h=struct.unpack('>II',b[16:24]); depth=b[24]
        require((w,h,depth)==(505,505,16),f'Heightmap unexpectedly {w}x{h}, {depth}-bit')
config=(ROOT/'Config/DefaultEngine.ini').read_text(encoding='utf-8-sig')
if 'GameDefaultMap=/Engine/Maps/Entry' in config:
    warnings.append('No saved NYVERRA map (.umap). Import heightmap, create and SAVE map in editor before playtesting.')
if not list((ROOT/'Content').rglob('*.umap')):
    warnings.append('No map asset packaged. Editor setup still required.')
print('C++ engine compilation: NOT TESTED (requires Unreal Engine and Windows toolchain).')
for w in sorted(set(warnings)): print('WARNING:',w)
for e in errors: print('ERROR:',e)
print('OFFLINE PREFLIGHT:', 'FAILED' if errors else 'PASSED')
sys.exit(bool(errors))
