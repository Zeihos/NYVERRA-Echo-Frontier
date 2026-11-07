"""Outside-UE integrity check for generated placement CSV."""
import csv, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / 'Content/TerrainSource/Foliage027/FoliagePlacements.csv'
with p.open(newline='',encoding='utf-8-sig') as f:
 rows=list(csv.DictReader(f))
assert len(rows)==540, f'expected 540 placements; got {len(rows)}'
assert set(r['Kind'] for r in rows) == {'Tree','Rock','Shrub'}
for r in rows:
 for col in ('X_cm','Y_cm','Z_cm','Yaw_deg','UniformScale'):float(r[col])
print('Validated',len(rows),'foliage placement records')
