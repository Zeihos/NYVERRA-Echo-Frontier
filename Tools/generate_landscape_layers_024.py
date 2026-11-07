"""Offline reproducible weightmap builder. Requires numpy and Pillow.
Run: python Tools/generate_landscape_layers_024.py
Does NOT modify the imported Unreal level.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'Content' / 'TerrainSource'
HEIGHT = ROOT / 'NyverraTestLandscape_505x505_R16.png'


def main():
    height_image = Image.open(HEIGHT)
    if height_image.size != (505, 505) or height_image.mode not in ('I;16', 'I'):
        raise ValueError('Expected a 505x505 16-bit heightmap')
    h = np.asarray(height_image, dtype=np.float64) / 65535.0
    gy, gx = np.gradient(h)
    slope = np.hypot(gx, gy)
    # Relative thresholds are chosen for this prototype heightmap, not world-space degrees.
    rock = np.clip((slope - 0.0014) / 0.0045, 0.0, 0.9)
    altitude = np.clip((h - 0.53) / 0.10, 0, 1)
    rock = np.maximum(rock, altitude * 0.65)
    yy, xx = np.indices(h.shape)
    variation = (np.sin(xx * 0.075) * np.cos(yy * 0.063) + 1.0) * 0.5
    grass = (1.0 - rock) * (0.62 + 0.25 * variation)
    soil = np.maximum(0, 1 - rock - grass)
    weights = np.stack([soil, grass, rock], axis=0)
    # Quantize while keeping the layers summing to 255 for every pixel.
    scaled = weights / weights.sum(axis=0, keepdims=True) * 255
    quant = np.floor(scaled).astype(np.uint8)
    residual = 255 - quant.astype(np.int16).sum(axis=0)
    # Largest-remainder correction, per pixel.
    order = np.argsort(-(scaled - quant), axis=0)
    for rank in range(3):
        mask = residual > rank
        rows, cols = np.where(mask)
        quant[order[rank, rows, cols], rows, cols] += 1
    assert np.all(quant.astype(np.int16).sum(axis=0) == 255)
    for channel, name in enumerate(('Soil', 'Grass', 'Rock')):
        path = ROOT / f'Nyverra_Weight_{name}_505.png'
        Image.fromarray(quant[channel], mode='L').save(path)
        print(name, path, 'range', int(quant[channel].min()), int(quant[channel].max()))


if __name__ == '__main__':
    main()
