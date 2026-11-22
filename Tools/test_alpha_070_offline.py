"""Tests for atomic map selection using temporary project folders."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

module_path = Path(__file__).with_name("set_test_world_default.py")
spec = importlib.util.spec_from_file_location("map_setup", module_path)
map_setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(map_setup)


class MapConfiguration(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "Config").mkdir()
        (self.root / "Content/Maps").mkdir(parents=True)
        self.ini = self.root / "Config/DefaultEngine.ini"
        self.ini.write_text(
            "[/Script/EngineSettings.GameMapsSettings]\n"
            "GameDefaultMap=/Engine/Maps/Entry\n"
            "EditorStartupMap=/Engine/Maps/Entry\n"
            "ServerDefaultMap=/Engine/Maps/Entry\n"
            "\n[Other.Section]\n"
            "GameDefaultMap=/DoNotModify\n",
            encoding="utf-8")

    def test_missing_map_refuses_update_without_backup(self):
        original = self.ini.read_bytes()
        with self.assertRaises(ValueError):
            map_setup.configure(self.root)
        self.assertEqual(original, self.ini.read_bytes())
        self.assertFalse(self.ini.with_suffix(".ini.bak").exists())

    def test_nonempty_saved_map_required(self):
        (self.root / "Content/Maps/TestWorld.umap").touch()
        with self.assertRaises(ValueError):
            map_setup.configure(self.root)

    def test_preserve_other_sections_and_repeated_run(self):
        (self.root / "Content/Maps/TestWorld.umap").write_bytes(b"map-fixture")
        self.assertTrue(map_setup.configure(self.root))
        result = self.ini.read_text(encoding="utf-8")
        self.assertEqual(3, result.count("=/Game/Maps/TestWorld"))
        self.assertIn("[Other.Section]\nGameDefaultMap=/DoNotModify", result)
        backup = self.ini.with_suffix(".ini.bak")
        old_backup = backup.read_bytes()
        self.assertFalse(map_setup.configure(self.root))
        self.assertEqual(old_backup, backup.read_bytes())

    def test_duplicate_section_key_rejected_without_partial_write(self):
        (self.root / "Content/Maps/TestWorld.umap").write_bytes(b"map")
        with self.ini.open("a", encoding="utf-8") as f:
            f.write("\n[/Script/EngineSettings.GameMapsSettings]\n")
        original = self.ini.read_bytes()
        with self.assertRaises(ValueError):
            map_setup.configure(self.root)
        self.assertEqual(original, self.ini.read_bytes())


if __name__ == "__main__":
    unittest.main()
