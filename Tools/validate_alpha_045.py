from pathlib import Path
p=Path(__file__).resolve().parents[1]
source=(p/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
checks={
 'ground trace ignores buildings':'GroundQuery.AddIgnoredActor(Surface)' in source,
 'map-authored spawn fallback':'keeping authored spawn elevation' in source,
 'slope test':'GroundHit.ImpactNormal.Z >= 0.7f' in source,
 'respawn does not use fixed Z':'RespawnLocation.Z = GroundHit.ImpactPoint.Z' in source,
 'uproject exists':(p/'NYVERRA.uproject').is_file(),
}
for key,result in checks.items(): print(('PASS' if result else 'FAIL'),key)
if not all(checks.values()): raise SystemExit(1)
print('Offline checks passed; Unreal compilation and runtime not tested.')
