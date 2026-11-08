"""NYVERRA visual asset import guardrails (offline; no UE editor required).

When the 0.55 asset pack is installed, also validate each 1024x1024 PNG header.
Python stdlib only; safe to run on GitHub Actions without texture pack.
"""
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Content" / "VisualPolishSource" / "Terrain"
IM = (ROOT / "Tools" / "import_visual_polish_055.py").read_text(encoding="utf-8")
AP = (ROOT / "Tools" / "apply_visual_polish_055.py").read_text(encoding="utf-8")


class VisualPolishTests(unittest.TestCase):
    def test_non_destructive_asset_directory(self):
        self.assertIn("/Game/NYVERRA/VisualPolish", IM)
        self.assertIn('"replace_existing", False', IM)
        self.assertIn("EDITOR.does_asset_exist(path)", IM)
        self.assertIn("raise RuntimeError", IM)

    def test_all_three_pbr_channels_and_three_terrain_layers(self):
        for part in ("Albedo", "Normal", "Roughness", "Grass", "Rock", "Soil"):
            self.assertIn(part, IM)
        for prop in ("MP_BASE_COLOR", "MP_NORMAL", "MP_ROUGHNESS"):
            self.assertIn(prop, IM)
        # Additive LandscapeLayerWeight would brighten diffuse and corrupt normals.
        self.assertIn("MaterialExpressionLandscapeLayerSample", IM)
        self.assertIn("MaterialExpressionLinearInterpolate", IM)
        self.assertNotIn("unreal.MaterialExpressionLandscapeLayerWeight", IM)

    def test_texture_color_space_is_explicit(self):
        self.assertIn("TC_NORMALMAP", IM)
        self.assertIn("TC_MASKS", IM)
        self.assertIn('"srgb", False', IM)

    def test_material_assignment_preserves_custom_maps_and_requires_save(self):
        self.assertIn("Custom landscape preserved", AP)
        self.assertIn("NY_PersistentGround_NavCollision", AP)
        self.assertIn("not saved", AP)
        self.assertNotIn("save_current_level", AP)

    def test_texture_source_set_if_installed(self):
        files = [
            SRC / ("T_Ny%s_%s.png" % (kind, channel))
            for kind in ("Soil", "Grass", "Rock")
            for channel in ("Albedo", "Normal", "Roughness")
        ]
        if not SRC.exists():
            self.skipTest("Optional 0.55 binary texture pack has not been committed yet")
        for file in files:
            self.assertTrue(file.is_file(), str(file))
            with file.open("rb") as f:
                header = f.read(24)
            self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">II", header[16:24]), (1024, 1024))


if __name__ == "__main__":
    unittest.main(verbosity=2)
