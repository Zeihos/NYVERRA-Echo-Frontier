"""Rebuild 505x505 NYVERRA landscape heightmap (deterministic, requires numpy Pillow scipy).
Usage: python Tools/generate_heightmap.py
UE landscape import heightmap is 16-bit grayscale PNG, 505x505.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
N=505
rng=np.random.default_rng(190019)
y,x=np.mgrid[:N,:N].astype(np.float32)
noise=np.zeros((N,N),np.float32)
for sigma,amp in [(88,12),(38,9),(16,5),(6,2),(2,0.6)]:
    a=gaussian_filter(rng.standard_normal((N,N)).astype(np.float32),sigma,mode='reflect')
    a/=max(float(a.std()),1e-5)
    noise+=amp*a
wx=(x-252)*(10000/504); wy=(y-252)*(10000/504)
h=noise+38
for cx,cy,r in [(0,0,900),(1750,1550,1150),(-2050,900,1300),(450,-2350,1080)]:
    d=np.hypot(wx-cx,wy-cy)
    t=np.clip((d-r)/400,0,1); t=t*t*(3-2*t)
    h=h*t+38*(1-t)
pixel=np.clip(np.rint(32768+(h-38)*128),0,65535).astype(np.uint16)
out=Path(__file__).resolve().parent.parent/'Content'/'TerrainSource'
out.mkdir(parents=True,exist_ok=True)
Image.fromarray(pixel,mode='I;16').save(out/'NyverraTestLandscape_505x505_R16.png')
print('Heightmap generated:',pixel.shape,int(pixel.min()),int(pixel.max()))
