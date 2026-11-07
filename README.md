# NYVERRA: Echo Frontier

Private Unreal Engine 5.8 C++ multiplayer survival prototype (Windows; PvP/PvE, building, crafting).

**Latest sources: Alpha 0.53 + UE 5.8 compilation fixes (Nov 2026).** The tester successfully rebuilt and launched the project in Unreal Engine 5.8 and manually verified single-player PIE movement, sprint/jump, harvesting, inventory and melee combat. This is **not a release**; two-player network correctness, dedicated-server build, packaging, and a checked-in TestWorld map are **not yet verified**.

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
