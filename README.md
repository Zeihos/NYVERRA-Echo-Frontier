# NYVERRA: Echo Frontier

Private Unreal Engine 5.8 C++ multiplayer survival prototype (Windows; PvP/PvE, building, crafting).

**Latest sources: Alpha 0.53.** Not a playable release. C++ compilation, UE Editor map generation, Windows launch, and two-player network correctness **are not yet verified**.

## First playable test map

On Windows with UE 5.8 and Visual Studio C++ tools:

1. Close Unreal Editor and run `BUILD_AND_PREPARE_ALPHA_053_WINDOWS.bat` next to `NYVERRA.uproject`.
2. If Unreal is installed elsewhere, pass the engine directory as argument, e.g. `BUILD_AND_PREPARE_ALPHA_053_WINDOWS.bat "D:\UE_5.8"`.
3. The script builds `NYVERRAEditor`, generates a saved `Content/Maps/TestWorld.umap` only if missing, and selects it as the Game/Editor/Server default map.
4. Open `NYVERRA.uproject`, build navigation paths and save `TestWorld` in Unreal Editor.
5. Run 2 players in PIE (Play As Listen Server) and record errors for the next development pass.

See `FIRST_PLAY_ALPHA_053_RU.txt` for more details. Failure logs: `BUILD_ALPHA_051.log`, `BUILD_ALPHA_051_ERRORS.txt`, `BUILD_ALPHA_053_MAP.log`.

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
