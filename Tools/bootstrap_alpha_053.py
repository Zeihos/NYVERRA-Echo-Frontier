"""UE5.8 Editor-only bootstrap: create/reuse TestWorld, set default maps.

Use UnrealEditor-Cmd.exe -ExecutePythonScript=... after NYVERRAEditor compiles.
Safe to re-run: existing TestWorld is never overwritten.
"""
from pathlib import Path
import runpy
import unreal

PROJECT_ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP_PATH = '/Game/Maps/TestWorld'
MAP_FILE = PROJECT_ROOT / 'Content' / 'Maps' / 'TestWorld.umap'
TOOLS = PROJECT_ROOT / 'Tools'

if not (PROJECT_ROOT / 'NYVERRA.uproject').is_file():
    raise RuntimeError('Not a NYVERRA project directory: ' + str(PROJECT_ROOT))

if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    unreal.log('[NYVERRA 0.53] TestWorld already exists; preserving all actors.')
else:
    unreal.log('[NYVERRA 0.53] Creating saved TestWorld with floor, nav bounds, and PlayerStarts...')
    runpy.run_path(str(TOOLS / 'create_test_world.py'), run_name='__main__')

if not MAP_FILE.is_file():
    raise RuntimeError('Expected a saved .umap but none exists: ' + str(MAP_FILE))

# Set editor/game/server defaults only after verifying the saved level.
# Uses the same safe, checked INI rewrite already provided in Alpha 0.52.
runpy.run_path(str(TOOLS / 'set_test_world_default.py'), run_name='__main__')
unreal.log('[NYVERRA 0.53] TestWorld map saved and assigned for game, editor and server.')
unreal.log_warning('[NYVERRA 0.53] Open map, Build > Build Paths, press P to inspect NavMesh, SAVE before PvE testing.')
