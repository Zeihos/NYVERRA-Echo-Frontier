from pathlib import Path
root = Path(__file__).resolve().parents[1]
character = (root / 'Source/NYVERRA/Private/NyCharacter.cpp').read_text()
game_mode = (root / 'Source/NYVERRA/Private/NyGameMode.cpp').read_text()
checks = {
    'server harvest verifies capacity before resource consumption': character.index('Capacity < Award') < character.index('Resource->Harvest(Harvested, Award)'),
    'harvest awards actual resource amount': 'AddItem(Item, Harvested)' in character,
    'respawn ignores player collisions': 'Surface->IsA<APawn>()' in character,
    'spawn ignores resources and enemies': 'Obstacle->IsA<ANyEnemy>()' in game_mode and 'Obstacle->IsA<ANyResource>()' in game_mode,
    'Unreal project exists': (root / 'NYVERRA.uproject').is_file(),
    'C++ build rules exist': (root / 'Source/NYVERRA/NYVERRA.Build.cs').is_file(),
}
for name, ok in checks.items(): print(('PASS' if ok else 'FAIL') + ' ' + name)
raise SystemExit(0 if all(checks.values()) else 1)
