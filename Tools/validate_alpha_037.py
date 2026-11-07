from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
required=['PreviewRemove(ENyItemId::Wood, WoodCost)', 'PreviewRemove(ENyItemId::Stone, StoneCost)', 'Preview.Num() >= MaxSlots', 'NyBuildingGround', 'GroundHit.ImpactNormal.Z < 0.85f']
for marker in required:
    assert marker in s, f'Missing code marker: {marker}'
for f in ['NYVERRA.uproject','Source/NYVERRA/NYVERRA.Build.cs','Source/NYVERRA/Private/NyGameMode.cpp']:
    assert (root/f).exists(), f'Missing: {f}'
print('Alpha 0.37 offline structural checks passed (not an Unreal compile).')
