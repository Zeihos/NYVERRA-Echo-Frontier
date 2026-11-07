"""Build deterministic tileable tangent-space normals and roughness from source albedo.
Run with Python 3, Pillow and numpy outside Unreal Editor.
"""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'Content'/'TerrainSource'/'Textures'
for name,strength,base_rough in [('Soil',2.5,0.87),('Grass',3.2,0.91),('Rock',4.5,0.79)]:
    rgb=np.asarray(Image.open(P/f'T_Ny{name}_Albedo.png').convert('RGB'),dtype=np.float32)/255.
    # Periodic finite differences ensure seamless wrap at tile edges.
    h=rgb @ np.array([.2126,.7152,.0722],dtype=np.float32)
    dx=(np.roll(h,-1,axis=1)-np.roll(h,1,axis=1))*strength
    dy=(np.roll(h,-1,axis=0)-np.roll(h,1,axis=0))*strength
    n=np.stack((-dx,-dy,np.ones_like(h)),axis=-1)
    n/=np.linalg.norm(n,axis=-1,keepdims=True)
    normal=np.uint8(np.clip((n*.5+.5)*255,0,255))
    Image.fromarray(normal,'RGB').save(P/f'T_Ny{name}_Normal.png')
    rough=np.uint8(np.clip(base_rough+(h-.5)*.09,.55,.98)*255)
    Image.fromarray(rough,'L').save(P/f'T_Ny{name}_Roughness.png')
    print(name, 'normal/roughness:', normal.shape)
