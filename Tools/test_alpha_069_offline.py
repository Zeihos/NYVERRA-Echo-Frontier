"""Unit tests for the map-readiness report using isolated synthetic fixtures."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT = Path(__file__).with_name("check_runtime_readiness.py")
spec = importlib.util.spec_from_file_location("readiness", SCRIPT)
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


class ReadinessChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "Config").mkdir()
        (self.root / "Content/Maps").mkdir(parents=True)
        (self.root / "NYVERRA.uproject").write_text(json.dumps({
            "EngineAssociation": "5.8", "Modules": [{"Name": "NYVERRA"}]
        }), encoding="utf-8")

    def configure(self, path="/Game/Maps/TestWorld"):
        (self.root / "Config/DefaultEngine.ini").write_text(
            "[/Script/EngineSettings.GameMapsSettings]\n"
            + "".join(f"{key}={path}\n" for key in readiness.MAP_KEYS),
            encoding="utf-8",
        )

    def test_missing_map_detected_even_with_valid_config(self):
        self.configure()
        warnings = readiness.inspect(self.root)
        self.assertEqual(3, len(warnings))
        self.assertTrue(all("absent" in w for w in warnings))

    def test_engine_entry_is_not_a_playable_project_map(self):
        self.configure("/Engine/Maps/Entry")
        warnings = readiness.inspect(self.root)
        self.assertEqual(3, len(warnings))
        self.assertTrue(all("not a packaged project map" in w for w in warnings))

    def test_existing_project_map_is_reported_as_present(self):
        self.configure()
        (self.root / "Content/Maps/TestWorld.umap").write_bytes(b"fixture")
        self.assertEqual([], readiness.inspect(self.root))

    def test_missing_settings_does_not_report_ready(self):
        (self.root / "Config/DefaultEngine.ini").write_text(
            "[/Script/EngineSettings.GameMapsSettings]\n",
            encoding="utf-8")
        self.assertEqual(3, len(readiness.inspect(self.root)))

    def test_missing_project_module_is_reported(self):
        self.configure()
        (self.root / "Content/Maps/TestWorld.umap").write_bytes(b"fixture")
        (self.root / "NYVERRA.uproject").write_text(json.dumps({
            "EngineAssociation": "5.8", "Modules": []
        }), encoding="utf-8")
        self.assertIn("NYVERRA runtime module missing from project",
                      readiness.inspect(self.root))


if __name__ == "__main__":
    unittest.main()
