# NYVERRA UE 5.8 — first-play QA / handoff

Session: 2026-11-07 (user's reported testing session)
Repository: `Zeihos/NYVERRA-Echo-Frontier`, `main`
Project: NYVERRA: Echo Frontier, Windows / Unreal Engine 5.8 / C++
Status: **Local editor and Play-in-Editor runtime verified by the tester; not a release.**

## Confirmed by tester on their Windows machine

- Project rebuilt successfully enough to launch Unreal Editor 5.8 and run the NYVERRA C++ game code in Play-in-Editor (PIE).
- Newly created `TestWorld` basic level showed the game HUD, dynamic world state, primitive resource nodes, and placeholder geometry.
- Tester explicitly marked each working:
  - WASD movement.
  - Shift sprint and Space jump.
  - E resource interaction/harvest.
  - I inventory.
  - Left-click melee attack against an enemy.
- These are **manual test reports**, not automated tests or independent proof of every game system.

## UE 5.8 C++ compilation fixes committed

- `Source/NYVERRAEditor.Target.cs` and `Source/NYVERRA.Target.cs`: `BuildSettingsVersion.V7`.
- `Source/NYVERRAServer.Target.cs`: `BuildSettingsVersion.V7` (updated to align the separate server target; dedicated-server build NOT tested).
- `NyLootCrate.cpp`, `NyResource.cpp`, `NyWorldState.cpp`, `NyBuildPiece.cpp`, `NyCharacter.cpp`, `NyEnemy.cpp`: rename the `GetLifetimeReplicatedProps` argument to `OutLifetimeProps` to match `DOREPLIFETIME`'s expected identifier.
- `NyWorldState.cpp`: replace unavailable `ADirectionalLight::GetDirectionalLightComponent()` with `GetComponent()`.
- `NyCharacter.cpp`: include `Engine/OverlapResult.h` for the complete `FOverlapResult` type.
- `NyEnemy.cpp`: avoid shadowing `AActor::Instigator` in `TakeDamage`.
- `NyGameMode.cpp`: use non-const navigation-system pointer when calling non-const `GetDefaultNavDataInstance`.
- `NyGameMode.h`: remove unimplemented `InitGame` override declaration.

## Verified GitHub repository facts / missing uploads

- `Source/`, `Config/`, `Content/TerrainSource/`, `Tools/`, `Documentation/`, Alpha notes and GitHub Actions offline Python test workflow are present.
- **No saved `Content/Maps/TestWorld.umap` in the repository tree** at this checkpoint. The level was created in Unreal Editor on the tester's machine; check that it has been saved via Ctrl+S before copying it to a Git checkout.
- Repository `Config/DefaultEngine.ini` still points to `/Engine/Maps/Entry` for startup/game/server; do not switch to TestWorld until its .umap is committed.
- The user's local project file is `NYVERRA_EchoFrontier.uproject`; repository project file is `NYVERRA.uproject`. The local test directory did not contain `.git`, so **local changes are not automatically synced**.
- `History/UE5_Alpha_Archives/` and its 52 historical UE5 source ZIPs have not been uploaded; only `History/Early_2D_Prototype/` is present.
- Test logs, local backup files, screenshot of play session, and local PowerShell repair scripts are **not** confirmed as repository files. They are not required to treat the source fixes as committed.

## Remaining issues and recommended next steps

1. Save and safely upload the current `TestWorld.umap` from the tester's computer (preserve any existing work); optionally upload related `Content/` assets. A separate local Git clone or GitHub Desktop is needed because the testing folder is not a checkout.
2. Resolve the screenshot warning about competing directional lights: Basic map already has DirectionalLight, while `ANyWorldState::CreateAtmosphere` creates its own. Choose one authoritative sun and verify weather/day-night visuals.
3. Set the saved TestWorld as startup map once the asset is committed and build/rebuild navigation on that map.
4. Verify PIE as listen server with 2 players, replication, loot/respawn, building/crafting, enemy AI navigation and health, death/respawn, dedicated-server build, and packaging. **None are confirmed by this test session.**
5. Improve gameplay visuals beyond primitives and implement remaining game roadmap from GDD; do not describe this as a finished playable release.
6. Complete historical archive upload separately if full version history is required.

## Handoff conclusion

Current `main` preserves the test-session C++ corrections and a written record of the successful manual core-gameplay tests. The exact **authored** test map and full historical archives are NOT preserved in GitHub yet.
