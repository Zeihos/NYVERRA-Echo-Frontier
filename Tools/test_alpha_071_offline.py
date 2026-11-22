"""Check Windows map bootstrap never claims success without strict readiness.

These are source checks, not Windows execution or Unreal compilation.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WindowsMapBootstrap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = (ROOT / "BUILD_AND_PREPARE_ALPHA_053_WINDOWS.bat").read_text(
            encoding="utf-8"
        )
        cls.bootstrap = (ROOT / "Tools/bootstrap_alpha_053.py").read_text(
            encoding="utf-8"
        )

    def test_strict_readiness_gate_before_success(self):
        text = self.batch
        self.assertIn('check_runtime_readiness.py" --strict', text)
        self.assertLess(text.index('check_runtime_readiness.py" --strict'),
                        text.index("echo [SUCCESS]"))
        self.assertIn("if errorlevel 1 (", text[text.index('check_runtime_readiness.py" --strict'):])
        self.assertNotIn("findstr /B /C:", text)

    def test_existing_map_is_not_recreated(self):
        script = self.bootstrap
        self.assertIn("does_asset_exist(MAP_PATH)", script)
        self.assertIn("else:", script)
        self.assertIn("runpy.run_path(str(TOOLS / 'create_test_world.py')", script)
        self.assertLess(script.index("does_asset_exist(MAP_PATH)"),
                        script.index("runpy.run_path(str(TOOLS / 'create_test_world.py')"))

    def test_map_exists_before_config_edit(self):
        script = self.bootstrap
        self.assertLess(script.index("if not MAP_FILE.is_file():"),
                        script.index("runpy.run_path(str(TOOLS / 'set_test_world_default.py')"))


if __name__ == "__main__":
    unittest.main()
