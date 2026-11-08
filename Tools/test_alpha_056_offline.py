"""Offline regression tests for NYVERRA Visual Polish 0.56. Stdlib only."""
from pathlib import Path
import importlib.util
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "Tools" / "validate_visual_pack_056.py"
spec = importlib.util.spec_from_file_location("nyverra_png_validation", VALIDATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(
        ">I", zlib.crc32(tag + data) & 0xFFFFFFFF
    )


def make_png(size=1024, channels=1):
    color = 0 if channels == 1 else 2
    header = struct.pack(">IIBBBBB", size, size, 8, color, 0, 0, 0)
    raw = (b"\x00" + b"\x80" * (size * channels)) * size
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


class TestVisual056Offline(unittest.TestCase):
    def with_file(self, payload, channel):
        with tempfile.TemporaryDirectory() as tmp:
            filename = Path(tmp) / ("T_NyGrass_%s.png" % channel)
            filename.write_bytes(payload)
            return module.verify_png(filename, channel)

    def test_valid_rgb_png(self):
        size, sha = self.with_file(make_png(channels=3), "Albedo")
        self.assertGreater(size, 500)
        self.assertEqual(len(sha), 64)

    def test_valid_grayscale_png(self):
        self.with_file(make_png(channels=1), "Roughness")

    def test_crc_corruption_rejected(self):
        data = bytearray(make_png(channels=3))
        data[30] ^= 7
        with self.assertRaises(ValueError):
            self.with_file(bytes(data), "Normal")

    def test_wrong_png_size_rejected(self):
        with self.assertRaises(ValueError):
            self.with_file(make_png(size=512, channels=3), "Albedo")

    def test_wrong_channel_type_rejected(self):
        with self.assertRaises(ValueError):
            self.with_file(make_png(channels=3), "Roughness")

    def test_non_destructive_editor_map(self):
        py = (ROOT / "Tools" / "finalize_visual_polish_056.py").read_text(encoding="utf-8")
        self.assertIn("new_level_from_template", py)
        self.assertIn('VISUAL_MAP = "/Game/Maps/TestWorld_Visual056"', py)
        self.assertIn('validator["main"]()', py)
        self.assertIn("Existing TestWorld_Visual056 preserved", py)
        self.assertNotIn("delete_asset(", py)
        self.assertLess(py.index('validator["main"]()'), py.index("import_visual_polish_055.py"))

    def test_windows_pipeline_guards(self):
        bat = (ROOT / "INSTALL_NYVERRA_VISUALS_056_WINDOWS.bat").read_text(encoding="utf-8")
        self.assertIn("validate_visual_pack_056.py", bat)
        self.assertIn("BUILD_ALPHA_051_WINDOWS.bat", bat)
        self.assertIn("TestWorld_Visual056.umap", bat)
        self.assertIn("VISUAL_POLISH_056_UNREAL.log", bat)
        self.assertIn("choice /C YN", bat)
        ps = (ROOT / "Tools" / "Sync-VisualPolish-ToGitHub.ps1").read_text(encoding="utf-8")
        self.assertIn('TestWorld_Visual056.umap', ps)
        self.assertIn("Get-Command git", ps)
        self.assertNotIn("push --force", ps)


if __name__ == "__main__":
    unittest.main(verbosity=2)
