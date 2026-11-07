# NYVERRA — Core systems polish QA and release gate

Checkpoint: 2026-11-08. Branch: `main`. Scope: *existing UE5.8 prototype*, not the full final game's GDD.

## Changes committed in this pass

| System | Change | Verification |
| --- | --- | --- |
| Resource harvesting | Final 1 item harvestable with axe or pickaxe; no permanent node depletion; 120 s server refill | Source invariant checked; UE runtime pending |
| Shared loot crates | Empty crates are invisible AND non-colliding until timed refill | Source invariant checked; 2-player PIE pending |
| PvE | Dead enemy disappears, stops blocking collision, respawns after 90 s at home with 60 health | Source invariant checked; NavMesh/PIE pending |
| World lighting | Reuse map-authored sun/fog; create placeholders only if absent | Source invariant checked; UE scene pending |
| Multiplayer respawn | Prefer PlayerStart with greatest clearance from living characters | Source invariant checked; PIE pending |
| Construction | Anchor 240 x 30 x 250 cm walls along any of four edges of 300 x 300 x 30 cm foundation | Source invariant checked; wall collision/PIE pending |
| HUD | Split controls into two lines, no crosshair over inventory, remove stale version label | Source invariant checked; visual resolutions pending |
| Source hygiene | Protect local logs / INI backups via .gitignore; provide safe map upload script | GitHub files checked; Windows PowerShell pending |

## Evidence / current limitations

- The tester's 2026-11-07 report confirms **on their Windows computer**: Unreal Editor launch and a local single-player PIE test of WASD, sprint, jump, E harvest, I inventory, and LMB combat.
- This report does **not** establish that the new changes above compile or behave correctly.
- `Content/Maps/TestWorld.umap` is NOT in GitHub at this checkpoint. The locally authored and tested file must be copied from the tester's PC.
- `Config/DefaultEngine.ini` still points to `/Engine/Maps/Entry` until the authored map is synced.
- 52 historical `History/UE5_Alpha_Archives` ZIPs are not committed; source files and documents ARE present.
- CI `.github/workflows/nyverra-offline.yml` runs source regression tests but its latest run result was **not** independently confirmed in this session.
- Realistic art, saving/loading, production servers, PvP balance, base raids, seasonal wipes and release packaging are **not complete**. The project is still a prototype.

## Reproducible checks (Windows)

From a clean local Git checkout (not the unrelated Unreal project folder):

```bat
git pull origin main
py -3 -m unittest discover -s Tools -p "test_alpha_*.py" -v
BUILD_AND_PREPARE_ALPHA_053_WINDOWS.bat
```

If the Windows-tested map already exists on disk and is NOT in the clone, preserve it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Tools\Sync-TestWorld-ToGitHub.ps1 -MapFile "C:\TESTED_PROJECT\Content\Maps\TestWorld.umap"
```

This script uploads only the saved map and default-map configuration (no assets beyond those two files). Any custom materials, meshes, or Blueprint dependencies need a separate asset upload.

## Manual two-player PIE acceptance checklist

1. Compile the latest `main` using Unreal Engine 5.8 and Visual Studio C++ toolchain. Save compiler errors if any.
2. Load the authored TestWorld; check PlayerStart positions, navigation bounds and absence of duplicate directional lights.
3. Play with **2 players** in listen-server mode. Both must move, jump and sprint correctly.
4. Mine a resource with the final remaining unit using an axe/pickaxe. Check exact inventory increment and synchronized empty/invisible node on both clients. Wait 120 s for the same node to reappear and become harvestable.
5. Loot the same crate with both players. Ensure a single reward, no collision when emptied and reappearance after its configured cooldown.
6. Craft tools with both ordinary and nearly full inventories. Reject craft when not enough resources/capacity, without losing ingredients.
7. Place a foundation and attach four walls one at a time around its edges. Try blocked locations, steep slopes, resources and other player bodies. Materials should only be spent on valid server placements.
8. Kill a PvE enemy and verify no collision or visibility for the dead actor; wait 90 s and test restored health, AI navigation and damage.
9. Have one player die; verify that respawn favors an unoccupied PlayerStart, restores survival stats, and does not keep the old inventory.
10. Confirm night/day/weather light changes without doubled suns. Test HUD at 1366x768 and 1920x1080, with inventory open and closed.
11. Repeat over standalone client/server and dedicated server after the PIE smoke test succeeds.
12. Build and test a packaged Windows game before calling anything release-ready.

## Stop conditions

Do not tag `v1.0`, publish a release, or claim full feature completion until: successful build and packaging, saved map+assets in GitHub, two-player tests, dedicated-server run, data persistence design, full GDD features and realistic assets are verified.
