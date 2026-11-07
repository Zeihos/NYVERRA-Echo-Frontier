#!/usr/bin/env python3
"""Offline NYVERRA source and content gate. No claims about UE compilation."""
from pathlib import Path
import csv, json, re, struct, sys
ROOT = Path(__file__).resolve().parents[1]
issues=[]
def check(ok, message):
    print(('PASS' if ok else 'FAIL')+' | '+message)
    if not ok: issues.append(message)
p=ROOT/'NYVERRA.uproject'
try:
    proj=json.loads(p.read_text(encoding='utf-8-sig'))
    check(any(x.get('Name')=='NYVERRA' for x in proj.get('Modules',[])), 'C++ runtime module declared')
except Exception as exc: check(False, f'uproject JSON: {exc}')
source=ROOT/'Source/NYVERRA'
for name in ['NyCharacter','NyEnemy','NyGameMode','NyWorldState','NyFoliageCluster','NyLootCrate']:
    check((source/'Private'/f'{name}.cpp').is_file() and (source/'Public'/f'{name}.h').is_file(), f'{name} source and header')
for cls in ['NYVERRA.Target.cs','NYVERRAEditor.Target.cs','NYVERRAServer.Target.cs']:
    check((ROOT/'Source'/cls).is_file(), cls)
height=ROOT/'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png'
try:
    h=height.read_bytes(); check(h[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',h[16:24])==(505,505) and h[24]==16, 'Landscape source PNG 505x505 / 16-bit')
except Exception as exc: check(False, f'Landscape: {exc}')
csv_path=ROOT/'Content/TerrainSource/Foliage027/FoliagePlacements.csv'
try:
    with csv_path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    check(len(rows)==540, f'foliage CSV count {len(rows)} (expected 540)')
except Exception as exc: check(False,f'foliage CSV: {exc}')
ini=(ROOT/'Config/DefaultEngine.ini').read_text(encoding='utf-8')
check('/Engine/Maps/Entry' in ini,'safe default Entry level specified')
levels=list((ROOT/'Content').rglob('*.umap'))
print(f'INFO | saved game .umap levels: {len(levels)}; Unreal Editor must author and save a map')
print('INFO | C++ compile, editor scripts, dedicated server, and multiplayer remain UNTESTED here')
print(f'RESULT | {len(issues)} offline validation failures')
sys.exit(1 if issues else 0)
