# NYVERRA — Visual Polish 0.56 installation and QA

New entry point: `INSTALL_NYVERRA_VISUALS_056_WINDOWS.bat` in the root of the Git repository.

## What is actually implemented

1. Checks all **9 PNGs**, 1024×1024 RGB/normal or grayscale/roughness, CRC32 and optionally SHA-256 from the included manifest.
2. Compiles `NYVERRAEditor` through the existing UE5.8 build script.
3. Imports PBR textures, material graphs and surface variants using `Tools/import_visual_polish_055.py`.
4. Creates **a new** `/Game/Maps/TestWorld_Visual056` map using UE5.8 `LevelEditorSubsystem.new_level_from_template`. Original `TestWorld` is not overwritten. On a clean project with no TestWorld, it creates a minimal fallback map first.
5. Applies PBR055 to recognized landscape/test floor in the visual map, without modifying unrelated artist materials.
6. Saves the new visual map and verifies the `.umap` and core material `.uasset` exist.
7. Prompts for OPTIONAL upload of terrain source PNGs, imported Unreal materials and `TestWorld_Visual056.umap` to the user's PRIVATE repo, through the existing protected PowerShell script. No forced Git push.

## Windows usage

- `git pull origin main`
- Extract `NYVERRA-Visual-Polish-0.56-READY.zip` **into your Git clone**, next to `NYVERRA.uproject`.
- Run `INSTALL_NYVERRA_VISUALS_056_WINDOWS.bat` (or the included `START_VISUAL_POLISH_056.bat`).
- In Unreal Editor, open `TestWorld_Visual056`, inspect PBR shading, day/night light, UV scale and performance, then run a 2-player PIE test.
- If prompted to upload, reconfirm that the destination repository is Private. Git push is non-force.

See `VISUAL_POLISH_055_STATUS.md` for previous design notes.

## Evidence and remaining limitations

- Python source and GitHub files have been verified; the earlier texture ZIP passed integrity and dimensions checks.
- **Real UE5.8 C++ compilation, Python editor automation, material shaders and saved-map generation have not been run in this environment.** The Windows script is a reproducible local validation path, not proof of success.
- The **9 PNGs and generated .uassets are not yet in GitHub**; they are in the separately provided ZIP, until the Windows step uploads them.
- An earlier user-authored TestWorld is not in GitHub either. The visual script creates a new copy locally without overwriting it.
- Models for player/enemies, high-detail trees, animations, metal/wood-specific material sets, optimization and release graphics remain incomplete. This is a polished prototype pass, not a finished visual release.

## Code and asset safety

- Does not overwrite old original texture or material assets.
- Fails on incomplete/corrupt PNGs before opening UE.
- Does not set TestWorld_Visual056 as the default level.
- Does not automatically publish assets without confirmation.
- Existing `TestWorld_Visual056` is preserved on rerun and will not be overwritten.
