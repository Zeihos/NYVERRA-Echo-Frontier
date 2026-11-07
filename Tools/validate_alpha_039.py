"""Offline source-level regression assertions (NOT a UE compilation)."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
h=(root/'Source/NYVERRA/Public/NyCharacter.h').read_text(encoding='utf-8')
c=(root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(encoding='utf-8')
checks={
 'sprint replicated with OnRep':'ReplicatedUsing=OnRep_Sprint' in h,
 'OnRep declared':'void OnRep_Sprint()' in h,
 'OnRep implementation':'void ANyCharacter::OnRep_Sprint()' in c,
 'replication registration':'DOREPLIFETIME(ANyCharacter,bWantsSprint)' in c,
 'sprint enforced server-side':'bSprinting&&!bIsDead&&Health>0.f&&Stamina>5.f' in c,
 'death resets sprint':'bWantsSprint=false;OnRep_Sprint();' in c,
 'dead player movement blocked':'if(!bIsDead&&Controller&&V!=0)' in c,
}
for key,valid in checks.items(): print(('PASS' if valid else 'FAIL'),key)
if not all(checks.values()): raise SystemExit(1)
