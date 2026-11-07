from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
checks={
 'rotation-aware overlap': 'Rot.Quaternion()' in s and 'OverlapMultiByObjectType' in s,
 'real mesh dimensions': 'FVector(150.f, 150.f, 15.f)' in s and 'FVector(150.f, 15.f, 125.f)' in s,
 'server-only building': 'ServerPlacePiece_Implementation' in s and '!HasAuthority()' in s,
 'inventory transaction': 'SpendItems(ENyItemId::Wood,4,ENyItemId::Stone,2)' in s,
 'existing build check': 'Other->IsA<ANyBuildPiece>()' in s,
}
for name,ok in checks.items(): print(('PASS' if ok else 'FAIL')+' '+name)
if not all(checks.values()): raise SystemExit(1)
