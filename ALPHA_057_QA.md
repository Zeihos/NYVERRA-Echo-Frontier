# NYVERRA: Echo Frontier — Alpha 0.57 QA

2026-11-08 • Private repo `Zeihos/NYVERRA-Echo-Frontier` • `main`

## Delivered in source

- `ENyItemId::Water` appended after existing item IDs; existing enum numbers unchanged.
- `ENyResourceKind::Water` appended after existing kinds.
- Server generates renewable water caches in wilderness and **six guaranteed locations**, including four close to starter spawns.
- Resource nodes have 120-second server respawn, no collision when empty, and replicated availability.
- `E` gathers clean water into the same atomic server-inventory transaction as other resources.
- `Q` consumes one water item on the server, restores up to 35 thirst, and cannot be used while dead, at full thirst, or without water. 0.6-second cooldown blocks rapid accidental double use.
- Inventory UI and HUD show water; aim at a node/crate for a context-specific interaction prompt.
- Opening inventory cancels sprint/jump and suppresses gameplay bindings (movement, attack, building, gathering and consumption).
- Optional prototype water/berry/Echo materials are built by `Tools/create_consumable_materials_057.py` during the **safe visual setup**. Existing custom materials are untouched.

## Local first-run gate (Windows)

From the Git clone root, after `git pull origin main`:

```bat
TEST_ALPHA_057_WINDOWS.bat
```

Runs Python syntax checks, offline source regression tests, then `NYVERRAEditor` compilation through the existing UE5.8 build wrapper. For a custom UE5.8 installation, pass its root path as the argument.

**The UE5.8 C++ build and tests below have NOT been performed in this environment.** Offline source tests do not prove the Unreal gameplay implementation.

## Manual multiplayer acceptance

1. Open your Unreal Editor 5.8 saved test map in Play-In-Editor with **two players**, Play As Listen Server.
2. Find a guaranteed fresh-water cache around (480,380), (-480,380), (-480,-380) or (480,-380) game centimeters. This uses a blue-tinted cylinder proxy when the optional resource materials have been imported.
3. Look at a water source: the HUD should display `E GATHER CLEAN WATER` with remaining units. Press E; both the water count in HUD/inventory and shared source quantity should update.
4. Wait for thirst below 100 and press Q. Exactly one water item must be removed; thirst rises by 35, clamped at 100. Test Q repeatedly and verify there is no free hydration.
5. Empty a source. It must be invisible/nonblocking on both players; it must respawn after around **120 seconds**, without duplication.
6. While the inventory is open, try WASD, LMB, Q, E, 1, 2, 3, 4, F and Shift. None should change server gameplay state; closing inventory should restore normal controls.
7. Two players mine the final remaining unit at the same time; server must award it to at most one player, with no item duplication.
8. Verify old survival mechanics: berries still restore hunger, resource/loot timers continue, enemy AI pursues and respawns, foundations and walls cost their usual materials.
9. If `TestWorld_Visual056` exists, run `Tools/finalize_visual_polish_056.py` again to create the three new resource materials (the authored map is preserved). Confirm Water blue, Berries red and Echo cyan in the Editor; all are still **prototype meshes**.
10. Perform a separate dedicated-server/packaged client test when editor PIE works. Save logs and captures for the next fix pass.

## Still blocked

- No verified compiled UE5.8 build of Alpha 0.57.
- User-authored test map and PBR PNG / imported `.uasset` materials remain unconfirmed in GitHub; follow the Visual Polish 0.56 upload workflow.
- No full animation, final character models, audio, long-term player persistence, production backend, base raids or wipe automation; this is NOT a release-ready game.
