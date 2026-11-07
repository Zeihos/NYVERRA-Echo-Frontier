from pathlib import Path
root = Path(__file__).resolve().parents[1]
code = (root / 'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
start = code.index('void ANyCharacter::ServerPlacePiece_Implementation')
end = code.index('void ANyCharacter::ServerInteract_Implementation', start)
section = code[start:end]
checks = {
    'post-success build cooldown': section.index('LastBuildTime = Now;') > section.index('Piece->Initialize(Type);'),
    'map bounds include footprint': '4350.f' in section,
    'server-side overlap handling': 'OverlapMultiByObjectType' in section,
    'server-side item transaction': 'SpendItems(ENyItemId::Wood,4,ENyItemId::Stone,2)' in section,
    'terrain ignored in overlap': 'Other == GroundHit.GetActor()' in section,
    'core project present': (root/'NYVERRA.uproject').exists(),
}
for name, passed in checks.items(): print(('PASS' if passed else 'FAIL') + ' ' + name)
if not all(checks.values()): raise SystemExit(1)
