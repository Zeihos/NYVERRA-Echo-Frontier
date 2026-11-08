# NYVERRA: Echo Frontier

Private Unreal Engine 5.8 C++ multiplayer survival prototype (Windows; PvP/PvE, building, crafting).

**Latest sources: Alpha 0.58 (prototype) + Unreal Engine 5.8 compilation fixes.** The tester successfully rebuilt and launched the project in Unreal Engine 5.8 and manually verified single-player PIE movement, sprint/jump, harvesting, inventory and melee combat. This is **not a release**; two-player network correctness, dedicated-server build, packaging, and a checked-in TestWorld map are **not yet verified**.

## First playable test map

On Windows with UE 5.8 and Visual Studio C++ tools:

1. Close Unreal Editor and run `BUILD_AND_PREPARE_ALPHA_053_WINDOWS.bat` next to `NYVERRA.uproject`.
2. If Unreal is installed elsewhere, pass the engine directory as argument, e.g. `BUILD_AND_PREPARE_ALPHA_053_WINDOWS.bat "D:\UE_5.8"`.
3. The script builds `NYVERRAEditor`, generates a saved `Content/Maps/TestWorld.umap` only if missing, and selects it as the Game/Editor/Server default map.
4. Open `NYVERRA.uproject`, build navigation paths and save `TestWorld` in Unreal Editor.
5. Run 2 players in PIE (Play As Listen Server) and record errors for the next development pass.

See `FIRST_PLAY_ALPHA_053_RU.txt` for more details. Failure logs: `BUILD_ALPHA_051.log`, `BUILD_ALPHA_051_ERRORS.txt`, `BUILD_ALPHA_053_MAP.log`.

**November 2026 first-play QA and handoff:** see [`QA_FIRST_PLAY_UE58_2026-11-07.md`](QA_FIRST_PLAY_UE58_2026-11-07.md). A local `TestWorld` was tested in PIE, but `Content/Maps/TestWorld.umap` is **not committed** yet; current repository startup settings still reference `/Engine/Maps/Entry`. The tester's local project was not a Git checkout, so local assets are not synchronized automatically.

## Source structure

- `Source/NYVERRA/` — game code for survival, AI, building, loot and replication.
- `Config/` — project settings and input.
- `Content/TerrainSource/` — terrain source art, not an authored `.umap` map.
- `Tools/` — offline generators, Unreal Editor Python scripts and tests.
- `Documentation/` — game design and technical specification (if included in your checkout).
- `History/Early_2D_Prototype/` — legacy historical prototype, not the current game.

### Earlier Alpha archives

The 52 historical Alpha ZIPs were **not uploaded** in the first GitHub commit. They are available in the separately supplied history archive parts. To preserve every binary archive in GitHub, upload `History/UE5_Alpha_Archives/` from the complete local package. Do not assume that the history folder already exists in this repository.

## Offline checks

`py -3 Tools/test_alpha_053_offline.py` — uses mock Unreal APIs to test map creation, re-run safety, INI update failure handling and two C++ source invariants. These tests are **not** an Unreal Engine compile or playtest.


## Core gameplay polish (8 November 2026)

The existing survival prototype was audited and the following **source-code fixes** are on `main`:

- Resources no longer get permanently destroyed on depletion: zero remaining hides and disables collision; after 120 s on the server they replenish and replicate the state.
- Empty shared loot crates also stop blocking collision until they refill.
- Mining with an axe/pickaxe can collect the final unit from a nearly empty node.
- Four initial PvE enemy actors now recover after 90 s, restoring health, navigation movement, visibility and collision across server/clients.
- Authored sun and fog actors are reused instead of unconditionally spawning duplicate lights.
- Respawn chooses a PlayerStart farthest from living players (best of the available starts).
- Walls can attach to the nearest side of a foundation and use corner-safe mesh extents.
- HUD controls were split into two readable lines; inventory no longer shows a combat crosshair.

These code changes have **not** been compiled or playtested in Unreal Editor after the changes. Offline tests check code structure, not runtime behavior.

### Windows checks

```bat
git pull origin main
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
```

GitHub Actions runs the same offline checks on push. A green offline workflow is **not** evidence of a working Unreal build.

### Authored TestWorld still needs upload

The tested `Content/Maps/TestWorld.umap` currently exists only on the tester's Windows machine, not this repository.

From a clean local clone, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Tools\Sync-TestWorld-ToGitHub.ps1 -MapFile "C:\PATH\TO\TESTED\PROJECT\Content\Maps\TestWorld.umap"
```

The script checks `main`, the exact remote, clean working tree and existing map hashes. It refuses to overwrite an unrelated map, updates all three default-map keys and pushes the authored `.umap`. Custom `.uasset` dependencies, if any, must be synced separately.

**Still unverified:** Windows C++ build after this polish pass; actual saved-map compatibility; two-player PIE networking; AI navigation after respawn; building four walls on a foundation; dedicated-server build; packaged game; release-quality visuals. The 52 historical Alpha ZIP archives are also still missing from GitHub.


## Visual polish 0.55 — 8 November 2026

**Code committed:** new versioned PBR import/assign tools, optional material hookups for existing 3D scenery, and color-coded HUD stat bars. Details: [VISUAL_POLISH_055_STATUS.md](VISUAL_POLISH_055_STATUS.md).

**External PNG package not committed yet:** download the NYVERRA 0.55 visual pack from the ChatGPT conversation, extract into your PRIVATE Git clone beside `NYVERRA.uproject`, then open Unreal Editor and run:

1. `Tools/import_visual_polish_055.py` to create `/Game/NYVERRA/VisualPolish/Textures` and `Materials`.
2. `Tools/apply_visual_polish_055.py` to assign material to recognized floor/landscape surfaces in the active map (no automatic level save).
3. Review the result, save the level, and use `Tools/Sync-VisualPolish-ToGitHub.ps1 -WithImportedAssets` from PowerShell to push the PNG and generated `.uasset` files.

**Important:** Gameplay source changes and import scripts are on GitHub now; the nine new PNGs, saved TestWorld and fully imported Unreal materials are NOT confirmed in the repository. High-quality foliage models, characters and enemies are still placeholders, and UE shader/Windows tests are pending.


## Visual polish 0.56 — 8 November 2026

**Current workflow:** Download `NYVERRA-Visual-Polish-0.56-READY.zip` from the conversation. Extract it into the root of your PRIVATE Git clone beside `NYVERRA.uproject`, then double-click `START_VISUAL_POLISH_056.bat`.

The launcher:
- pulls `main`, validates 9 1024px PNG textures against PNG CRC and SHA-256,
- builds the current Unreal Engine 5.8 editor target,
- creates **new PBR056 material assets** without overwriting old PBR055,
- creates and saves **`TestWorld_Visual056.umap` as a separate level** while preserving original TestWorld,
- offers an optional confirmed upload of texture PNGs, generated `.uasset` materials, and test maps to your PRIVATE GitHub repository.

No force push, no automatic override of startup maps. See [VISUAL_POLISH_056_STATUS.md](VISUAL_POLISH_056_STATUS.md).

**Limitations:** The archive's PNG binary assets are still local-only until uploaded on Windows; the Unreal shader compilation, gameplay rendering and server behavior have not been verified in this environment. 3D character models, foliage detail, animations, and release-quality graphics are not finished.


## Alpha 0.57 — renewable hydration and interaction UX

**Current source changes (8 November 2026):** A missing survival gameplay loop has been closed: renewable water nodes, server-validated `Q` drinking (one item restores 35 thirst), four guaranteed sources near spawn and additional POI/wilderness supplies. Existing inventory, replication, anti-duplication checks and resource regeneration are reused. Aiming at an interactable now shows its name and remaining quantity. Inventory focus blocks combat/movement actions and drops sprint.

`Tools/create_consumable_materials_057.py` adds non-destructive prototype Water/Berries/Echo PBR colors. The latest Visual Polish 0.56 installer calls this script automatically through `Tools/finalize_visual_polish_056.py` when source textures have been supplied.

**Windows check:** after `git pull origin main`, run `TEST_ALPHA_057_WINDOWS.bat`. This runs all offline tests and attempts a genuine Unreal Editor build. Then follow [ALPHA_057_QA.md](ALPHA_057_QA.md) for manual two-player tests. Neither compilation nor multiplayer success has been independently confirmed for 0.57.


## Alpha 0.58 — base raids and owner repairs

The multiplayer construction prototype now has server-owned durability and raids:

- Foundation **600 HP**, wall **360 HP**. HP and builder PlayerState are replicated.
- A player can melee a visible structure for **35 damage** per validated server hit. Destroying a piece at 0 HP removes it for all connected players.
- Builders can press **R** to repair their own damaged piece for **1 wood + 1 stone**, restoring up to **75 HP**, but only **12 seconds** after the last attack.
- The HUD shows visible structure HP and a green/amber/red condition bar. Clients send no structure reference or HP amount to the server for repair.

After `git pull origin main`, run `TEST_ALPHA_058_WINDOWS.bat` on a Windows computer with Unreal Engine 5.8 to execute offline checks and build `NYVERRAEditor`. Then follow [ALPHA_058_QA.md](ALPHA_058_QA.md) for the **two-player** manual raid/repair tests. The current GitHub source edits have not yet been independently compiled or tested in Unreal Engine.

**Still absent:** permanent account/ownership persistence, raid explosives, doors, raid loot, full multiplayer server QA, finished realistic assets and a packaged game. The tested `TestWorld.umap` and PBR source textures also need to be synchronized from Windows.
