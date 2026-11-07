from pathlib import Path
root = Path(__file__).resolve().parent.parent
cpp = (root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
h = (root/'Source/NYVERRA/Public/NyCharacter.h').read_text(encoding='utf-8')
checks = {
 'build RPC cooldown': 'Now - LastBuildTime < 0.35f' in cpp,
 'cooldown declared': 'float LastBuildTime=-100.f;' in h,
 'map boundaries': 'FMath::Abs(P.X)>4500.f' in cpp,
 'spending rollback': 'Piece->Destroy(); return;' in cpp,
 'uproject': (root/'NYVERRA.uproject').is_file(),
 'landscape source': (root/'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png').is_file(),
}
for name, ok in checks.items(): print(('PASS' if ok else 'FAIL'), name)
if not all(checks.values()): raise SystemExit(1)
print('Static checks only: Unreal compilation has not been performed.')
