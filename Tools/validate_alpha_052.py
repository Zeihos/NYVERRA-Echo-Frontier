from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/'Source/NYVERRA/Private/NyGameMode.cpp').read_text(encoding='utf-8')
checks={
 'fallback helper exists': 'static void NyEnsureFallbackPlayerStarts(UWorld* World)' in s,
 'fallback called in BeginPlay': 'NyEnsureFallbackPlayerStarts(GetWorld());' in s,
 'fallback not in InitGame': 'void ANyGameMode::InitGame(' not in s,
 'existing PlayerStart respected': 'TActorIterator<APlayerStart> It(World)' in s,
 'build script present': (p/'BUILD_ALPHA_051_WINDOWS.bat').exists(),
 'unreal project exists': (p/'NYVERRA.uproject').exists()
}
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+' '+k)
raise SystemExit(0 if all(checks.values()) else 1)
