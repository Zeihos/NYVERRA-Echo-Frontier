"""Offline integrity checks only; not an Unreal C++ compile."""
from pathlib import Path
import json, re, sys, zipfile
root=Path(__file__).resolve().parents[1]
checks={
 'uproject_json': lambda: json.loads((root/'NYVERRA.uproject').read_text())['Modules'][0]['Name']=='NYVERRA',
 'engine_version': lambda: json.loads((root/'NYVERRA.uproject').read_text())['EngineAssociation']=='5.8',
 'editor_target': lambda: (root/'Source/NYVERRAEditor.Target.cs').exists(),
 'server_target': lambda: (root/'Source/NYVERRAServer.Target.cs').exists(),
 'jump_input_guard': lambda: 'this,&ANyCharacter::TryJump' in (root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(),
 'jump_declared':lambda: 'void TryJump();' in (root/'Source/NYVERRA/Public/NyCharacter.h').read_text(),
 'dead_jump_blocked':lambda: '!bIsDead && Health>0.f' in (root/'Source/NYVERRA/Private/NyCharacter.cpp').read_text(),
 'maps_not_misconfigured': lambda: (root/'Content/Maps/TestWorld.umap').exists() or '/Engine/Maps/Entry' in (root/'Config/DefaultEngine.ini').read_text(),
}
failed=[]
for name,fn in checks.items():
 try: ok=bool(fn())
 except Exception as exc: ok=False; print(f'{name}: ERROR {exc}')
 print(f'{name}: {"PASS" if ok else "FAIL"}')
 if not ok:failed.append(name)
print(f'{len(checks)-len(failed)}/{len(checks)} offline checks passed. Unreal compile and gameplay UNTESTED.')
sys.exit(1 if failed else 0)
