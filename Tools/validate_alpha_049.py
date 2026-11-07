from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = (root / 'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
assert 'GetCollisionResponseToChannel(ECC_WorldDynamic) == ECR_Block' in source
assert 'Other == GroundHit.GetActor()' in source
assert 'OverlapMultiByObjectType' in source
assert (root/'NYVERRA.uproject').exists()
print('Alpha 0.49 offline guards: PASS (not an Unreal compile)')
