from pathlib import Path
import re, zipfile
root=Path(__file__).resolve().parents[1]
character=(root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
checks={
 'respawn from PlayerStart': 'TActorIterator<APlayerStart>' in character,
 'respawn ground trace uses playerstart XY': 'FVector(RespawnLocation.X,RespawnLocation.Y,50000.f)' in character,
 'build ground skips site geometry': 'GroundParams.AddIgnoredActor(HitActor)' in character,
 'server build validation preserved': 'ServerPlacePiece_Implementation' in character and 'SpendItems(ENyItemId::Wood,4,ENyItemId::Stone,2)' in character,
 'game target present': (root/'Source/NYVERRA.Target.cs').is_file(),
 'editor target present': (root/'Source/NYVERRAEditor.Target.cs').is_file(),
 'unreal project present': (root/'NYVERRA.uproject').is_file(),
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
print('C++ compilation and UE runtime tests: NOT PERFORMED')
raise SystemExit(not all(checks.values()))
