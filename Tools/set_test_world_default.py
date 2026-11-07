"""Outside Unreal Editor: set TestWorld as default ONLY once its .umap exists."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
world = root / 'Content/Maps/TestWorld.umap'
ini = root / 'Config/DefaultEngine.ini'
if not world.is_file():
    raise SystemExit('ERROR: saved Content/Maps/TestWorld.umap not found. Create and save level in Unreal first.')
if not ini.is_file():
    raise SystemExit('ERROR: Config/DefaultEngine.ini not found.')
content = ini.read_text(encoding='utf-8-sig')
updated = content
for key in ('GameDefaultMap', 'EditorStartupMap', 'ServerDefaultMap'):
    import re
    updated, count = re.subn(r'(?m)^' + key + r'=.*$', key + '=/Game/Maps/TestWorld', updated)
    if count != 1:
        raise SystemExit('ERROR: expected exactly one ' + key + ' entry; file unchanged.')
if updated != content:
    ini.with_suffix('.ini.bak').write_text(content, encoding='utf-8')
    ini.write_text(updated, encoding='utf-8')
print('OK: TestWorld assigned as startup/editor/server map. Backup: Config/DefaultEngine.ini.bak')
