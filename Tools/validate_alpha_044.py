"""Offline source invariants, not an Unreal compilation test."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
character = (root / 'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
checks = {
    'site geometry collision gate': 'Other->ActorHasTag(TEXT("NYVERRA_SiteGeometry"))' in character,
    'loot crate distance gate': 'DistSquared(GetActorLocation(), Crate->GetActorLocation())' in character,
    'view origin server gate': 'DistSquared(Eye, GetActorLocation())' in character,
    'server inventory atomic removal': 'SpendItems(ENyItemId::Wood,4,ENyItemId::Stone,2)' in character,
    'unreal project descriptor': (root / 'NYVERRA.uproject').is_file(),
    'build target': (root / 'Source/NYVERRA.Target.cs').is_file(),
}
for label, ok in checks.items():
    print(('PASS' if ok else 'FAIL') + ': ' + label)
if not all(checks.values()):
    raise SystemExit(1)
print('Offline checks passed. UE5 compilation and runtime NOT verified.')
