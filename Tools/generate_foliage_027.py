"""Generate deterministic, terrain-aware foliage placement data. Requires Pillow, NumPy."""
from pathlib import Path
import csv, math
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
TERRAIN=ROOT/'Content'/'TerrainSource'
OUT=TERRAIN/'Foliage027'
OUT.mkdir(parents=True,exist_ok=True)
p=np.asarray(Image.open(TERRAIN/'NyverraTestLandscape_505x505_R16.png'),dtype=np.uint16)
assert p.shape==(505,505) and p.dtype==np.uint16
# Landscape import scale: X/Y = 10000 / 504 cm; Z = 100 cm.
cm_per_pixel=10000.0/504.0
z_cm=(p.astype(np.float64)-32768.0)/128.0*100.0
grad_y,grad_x=np.gradient(z_cm,cm_per_pixel)
slope=np.hypot(grad_x,grad_y)
rng=np.random.default_rng(270027)
# Do not clutter landmarks or player spawn; coordinates expressed in cm.
reserved=[(0,0,900),(1750,1550,1150),(-2050,900,1300),(450,-2350,1080)]
items=[]
for kind,target,slope_max,min_sep in [('Tree',240,0.55,180),('Rock',110,1.15,105),('Shrub',190,0.85,85)]:
    accepted=[]
    for _ in range(70000):
        if len(accepted)>=target: break
        ix=int(rng.integers(10,495)); iy=int(rng.integers(10,495))
        x=(ix-252)*cm_per_pixel; y=(iy-252)*cm_per_pixel
        if any(math.hypot(x-cx,y-cy)<r for cx,cy,r in reserved): continue
        if slope[iy,ix] > slope_max: continue
        if kind in ('Tree','Shrub') and (x < -2800 and y > 500): continue
        if any((x-ax)**2+(y-ay)**2<min_sep**2 for ax,ay in accepted): continue
        accepted.append((x,y))
        scale=float(rng.uniform(0.85,1.25)) if kind!='Rock' else float(rng.uniform(0.7,1.7))
        items.append((kind,round(x,2),round(y,2),round(float(z_cm[iy,ix]),2),round(float(rng.uniform(0,360)),2),round(scale,3)))
    if len(accepted)!=target: raise RuntimeError(f'Placement deficit: {kind}: {len(accepted)}/{target}')
with (OUT/'FoliagePlacements.csv').open('w',newline='',encoding='utf-8') as fh:
    w=csv.writer(fh); w.writerow(['Kind','X_cm','Y_cm','Z_cm','Yaw_deg','UniformScale']); w.writerows(items)
preview=Image.new('RGB',(505,505),(38,48,42))
d=ImageDraw.Draw(preview)
colors={'Tree':(56,170,91),'Rock':(170,170,165),'Shrub':(122,171,89)}
for kind,x,y,z,yaw,scale in items:
    i=int(round(x/cm_per_pixel+252)); j=int(round(y/cm_per_pixel+252))
    d.ellipse((i-2,j-2,i+2,j+2),fill=colors[kind])
for cx,cy,r in reserved:
    i=cx/cm_per_pixel+252;j=cy/cm_per_pixel+252;rad=r/cm_per_pixel
    d.ellipse((i-rad,j-rad,i+rad,j+rad),outline=(241,190,80),width=2)
preview.save(OUT/'FoliagePreview.png')
print(f'Created {len(items)} positions (Tree 240 / Rock 110 / Shrub 190)')
