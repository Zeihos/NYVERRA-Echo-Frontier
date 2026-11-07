"""Verify terrain asset sizes, weightmaps and basic project structure offline."""
from pathlib import Path
from PIL import Image
import numpy as np
r = Path(__file__).resolve().parents[1]
assert (r / 'NYVERRA.uproject').is_file()
assert (r / 'Source/NYVERRA/Private/NyCharacter.cpp').is_file()
assert (r / 'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png').is_file()
layers = [np.asarray(Image.open(r / f'Content/TerrainSource/Nyverra_Weight_{name}_505.png'), dtype=np.uint16) for name in ('Soil','Grass','Rock')]
assert all(l.shape == (505,505) for l in layers)
assert np.all(sum(layers) == 255)
print('PASS: project structure, 505x505 maps, exact weight sum 255')
