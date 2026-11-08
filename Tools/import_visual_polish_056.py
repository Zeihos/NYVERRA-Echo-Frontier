"""Versioned PBR056 build, preserving all previously generated PBR055 materials.

Loads the shared Unreal material builder without running its module entrypoint,
then selects a new material version. Reuses the 9 source textures.
"""
from pathlib import Path
import importlib.util
import unreal

SCRIPT = Path(__file__).resolve().parent / "import_visual_polish_055.py"
spec = importlib.util.spec_from_file_location("nyverra_pbr_legacy_builder", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load NYVERRA PBR material builder")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.VERSION = "056"

if __name__ == "__main__":
    module.main()
    unreal.log("[NYVERRA VISUAL 056] Versioned PBR056 materials ready; old PBR055 untouched.")
