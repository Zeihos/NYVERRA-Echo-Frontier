"""NYVERRA Visual Polish 0.56: checked import into a NEW copy of TestWorld.

Run with Unreal Editor Python Script plugin:
  UnrealEditor-Cmd.exe NYVERRA.uproject -ExecutePythonScript="<root>/Tools/finalize_visual_polish_056.py"

Does not overwrite TestWorld or any custom /Game maps.
If TestWorld_Visual056 exists, refuses to modify it.
No global default-map changes; manual review required.
"""
from pathlib import Path
import runpy
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
TOOLS = ROOT / "Tools"
SOURCE_MAP = "/Game/Maps/TestWorld"
VISUAL_MAP = "/Game/Maps/TestWorld_Visual056"
VISUAL_DISK = ROOT / "Content" / "Maps" / "TestWorld_Visual056.umap"
E = unreal.EditorAssetLibrary
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def main():
    if not (ROOT / "NYVERRA.uproject").is_file():
        raise RuntimeError("Wrong project directory: " + str(ROOT))

    # Validate PNGs BEFORE creating or modifying any level or imported asset.
    validator = runpy.run_path(str(TOOLS / "validate_visual_pack_056.py"),
                               run_name="nyverra_validator")
    validator["main"]()

    # Asset imports are idempotent and must run even if the visual map already
    # exists (e.g. after an interrupted first import).
    runpy.run_path(str(TOOLS / "import_visual_polish_056.py"), run_name="__main__")
    # The 0.57 gameplay pass uses optional colored resource materials.
    # Re-runs preserve previously edited assets and authored levels.
    runpy.run_path(str(TOOLS / "create_consumable_materials_057.py"),
                   run_name="__main__")

    if E.does_asset_exist(VISUAL_MAP):
        unreal.log_warning("[NYVERRA VISUAL] Existing TestWorld_Visual056 preserved. No level changes.")
        if not VISUAL_DISK.is_file():
            raise RuntimeError("Editor reports a visual map, but its .umap is missing")
        return

    # Keep an authored TestWorld untouched. A fallback test map is only
    # generated on a clean project without ANY TestWorld asset.
    if not E.does_asset_exist(SOURCE_MAP):
        unreal.log_warning("[NYVERRA VISUAL] TestWorld absent; creating minimal test map first.")
        runpy.run_path(str(TOOLS / "create_test_world.py"), run_name="__main__")

    if not E.does_asset_exist(SOURCE_MAP):
        raise RuntimeError("TestWorld missing after attempted creation")

    # UE5.8 subsystem API: creates a new level from an existing template and
    # leaves the original level package byte-for-byte unchanged.
    if not LEVELS.new_level_from_template(VISUAL_MAP, SOURCE_MAP):
        raise RuntimeError("Could not create separate visual test level " + VISUAL_MAP)
    if not E.does_asset_exist(VISUAL_MAP):
        raise RuntimeError("New visual test level not visible to AssetRegistry")

    runpy.run_path(str(TOOLS / "apply_visual_polish_056.py"), run_name="__main__")

    if not LEVELS.save_current_level():
        raise RuntimeError("Could not save visual level (original TestWorld is still preserved)")
    if not VISUAL_DISK.is_file():
        raise RuntimeError("Expected saved visual .umap at " + str(VISUAL_DISK))

    unreal.log("[NYVERRA VISUAL] Created and saved: " + VISUAL_MAP)
    unreal.log_warning(
        "[NYVERRA VISUAL] Review terrain materials and textures in the editor, "
        "build navigation, test 2 players, then upload Content/Maps/TestWorld_Visual056.umap "
        "and Content/NYVERRA/VisualPolish .uassets to private GitHub."
    )

if __name__ == "__main__":
    main()
