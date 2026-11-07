from pathlib import Path
from collections import Counter
import csv,math
from PIL import Image
root=Path(__file__).resolve().parents[1]
p=root/'Content/TerrainSource/Foliage027/FoliagePlacements.csv'
with p.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
counts=Counter(r['Kind'] for r in rows)
assert counts=={'Tree':240,'Rock':110,'Shrub':190},counts
reserved=[(0,0,900),(1750,1550,1150),(-2050,900,1300),(450,-2350,1080)]
for r in rows:
 x=float(r['X_cm']); y=float(r['Y_cm']); z=float(r['Z_cm'])
 assert abs(x)<5001 and abs(y)<5001 and math.isfinite(z)
 assert all(math.hypot(x-cx,y-cy)>=rad for cx,cy,rad in reserved)
assert Image.open(p.parent/'FoliagePreview.png').size==(505,505)
print('Foliage data OK',dict(counts))
