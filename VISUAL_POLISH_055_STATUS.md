# NYVERRA — Visual polish checkpoint 0.55

Date: 2026-11-08. Repository: `Zeihos/NYVERRA-Echo-Frontier`, branch `main`.

## Verified GitHub state

- Repository visibility was **Private** when inspected.
- Current source contains C++ gameplay fixes, authored-map migration tool, editor material scripts, and offline test workflow.
- The previously tested `Content/Maps/TestWorld.umap` was **not in GitHub** when checked. Runtime level and two-client graphics remain unverified.
- `Content/VisualPolishSource/Terrain/` **is not in GitHub yet**. Image binary assets are supplied in a separate downloadable package and require a one-time local Git upload.
- 52 historical Alpha ZIPs were also absent when checked; unrelated to the PBR pass.

## Visual improvements implemented in source

- `Tools/import_visual_polish_055.py` creates nine imported textures and three PBR surface materials plus a three-layer Landscape material in NEW paths under `/Game/NYVERRA/VisualPolish`; old assets are not overwritten.
- Each material connects Albedo, Normal and Roughness with world-space UV tiling (400 cm); Normal and Roughness are imported with non-sRGB settings.
- The Landscape uses explicit Grass and Rock layer **samples** and two interpolations per channel. It does NOT incorrectly add surface colors on top of soil.
- `Tools/apply_visual_polish_055.py` can apply PBR to the current NYVERRA Landscape and/or the known `NY_PersistentGround_NavCollision` test floor. It preserves unrelated artist materials and does not auto-save a map.
- Runtime C++ now attempts to use imported PBR surface assets on instanced forests, shrubs, distant ridges, rocks, location beacon and Stone/Wood resource prototypes. Missing optional assets leave the original fallback visuals.
- `NyHUD.cpp` includes graphical status bars for health, hunger, thirst and stamina; it no longer shows those metrics as a single cramped line.

## Deliverable texture package

A separate `NYVERRA-Visual-Polish-0.55.zip` was prepared containing:

| Layer | 1024 px Albedo | Synthetic Normal | Synthetic Roughness |
|---|---|---|---|
| Grass | yes | yes | yes |
| Rock | yes | yes | yes |
| Soil | yes | yes | yes |

Albedo textures were created from generated terrain imagery with edge-seam reduction. Normal and roughness images are **derived approximations**, not physically calibrated scans. Art approval and checking tiling artifacts in Unreal remain necessary. A contact sheet is included.

## Installation in a clean Windows clone

1. `git pull origin main`.
2. Extract the visual pack **into the root of the clone**, preserving `Content/VisualPolishSource/Terrain/`.
3. In Unreal Editor 5.8 run `Tools/import_visual_polish_055.py` with **Tools > Execute Python Script**.
4. Open your saved level and run `Tools/apply_visual_polish_055.py`.
5. Confirm material compilation, level appearance, lights, UV scale and performance. Save the level ONLY after visual inspection.
6. Upload imported texture sources and generated `.uasset` files by running:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\Tools\Sync-VisualPolish-ToGitHub.ps1 -WithImportedAssets
   ```
7. Confirm the GitHub tree contains `Content/VisualPolishSource/Terrain` and `Content/NYVERRA/VisualPolish`. Check that the GitHub Actions offline tests pass.

## Incomplete / blockers

- No independent UE5.8 shader compilation or on-map screenshot of PBR055 materials has been obtained.
- The local authored `TestWorld.umap` remains to be uploaded through the separate safe sync workflow.
- Decorative forest trees, berry nodes, enemies, weapon meshes and buildings still use low-poly/primitives; these will require proper mesh/rig/animation work, not merely texture replacement.
- Unreal packaging and 2-client runtime tests are outstanding. This is **NOT a finished visual release**.
