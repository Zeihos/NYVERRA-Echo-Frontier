"""Create deterministic, tileable procedural ground albedo textures (Pillow, numpy)."""
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / 'Content' / 'TerrainSource' / 'Textures'
OUT.mkdir(parents=True, exist_ok=True)
N = 512

def seamless_noise(seed, power):
    rng = np.random.default_rng(seed)
    # Each frequency tiles exactly across the square and is blended cyclically.
    field = np.zeros((N,N),dtype=np.float32)
    total=0
    for freq,weight in [(4,0.45),(16,0.29),(64,0.17),(128,0.09)]:
        mini = rng.random((freq,freq),dtype=np.float32)
        yy,xx=np.meshgrid(np.arange(N)/N*freq,np.arange(N)/N*freq,indexing='ij')
        yi=np.floor(yy).astype(int); xi=np.floor(xx).astype(int)
        dy=yy-yi;dx=xx-xi
        dy=dy*dy*(3-2*dy);dx=dx*dx*(3-2*dx)
        v=(mini[yi%freq,xi%freq]*(1-dy)*(1-dx)+mini[(yi+1)%freq,xi%freq]*dy*(1-dx)+mini[yi%freq,(xi+1)%freq]*(1-dy)*dx+mini[(yi+1)%freq,(xi+1)%freq]*dy*dx)
        field+=v*weight;total+=weight
    return np.clip(((field/total)-0.5)*power,-0.5,0.5)

for label,base,seed in [('Soil',(88,68,52),121),('Grass',(71,97,57),229),('Rock',(112,115,117),337)]:
    coarse=seamless_noise(seed,1.3)
    detail=seamless_noise(seed+7,0.35)
    a=np.array(base,dtype=np.float32)[None,None,:]*(1+coarse[:,:,None]*0.48+detail[:,:,None]*0.25)
    if label=='Grass':
        a[:,:,1] *= 1+np.maximum(coarse,0)*0.16
    a=np.uint8(np.clip(a,0,255))
    path=OUT/f'T_Ny{label}_Albedo.png'
    Image.fromarray(a,'RGB').save(path)
    print(path.name,a.shape)
