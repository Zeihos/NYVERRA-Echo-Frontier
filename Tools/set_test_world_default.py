"""Select saved TestWorld as default only after verifying the actual map file.

The edit is constrained to GameMapsSettings, idempotent and atomic. It does not
silently change unrelated INI sections, and keeps a backup of the previous file.
Run outside Unreal Editor after the editor has successfully saved the map.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SECTION = "[/Script/EngineSettings.GameMapsSettings]"
KEYS = ("GameDefaultMap", "EditorStartupMap", "ServerDefaultMap")
VALUE = "/Game/Maps/TestWorld"


def configure(root: Path) -> bool:
    world = root / "Content/Maps/TestWorld.umap"
    ini = root / "Config/DefaultEngine.ini"
    if not world.is_file() or world.stat().st_size == 0:
        raise ValueError("Saved nonempty Content/Maps/TestWorld.umap not found")
    if not ini.is_file():
        raise ValueError("Config/DefaultEngine.ini not found")
    original = ini.read_text(encoding="utf-8-sig")
    lines = original.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.strip() == SECTION]
    if len(starts) != 1:
        raise ValueError("Expected exactly one GameMapsSettings section")
    begin = starts[0] + 1
    end = next((i for i in range(begin, len(lines))
                if re.match(r"^\s*\[", lines[i])), len(lines))
    found = {}
    for index in range(begin, end):
        for key in KEYS:
            if re.match(r"^\s*" + re.escape(key) + r"\s*=", lines[index]):
                found.setdefault(key, []).append(index)
    if any(len(found.get(key, [])) != 1 for key in KEYS):
        raise ValueError("Expected exactly one entry per map key inside GameMapsSettings")
    for key in KEYS:
        index = found[key][0]
        newline = "\r\n" if lines[index].endswith("\r\n") else ("\n" if lines[index].endswith("\n") else "")
        lines[index] = f"{key}={VALUE}{newline}"
    updated = "".join(lines)
    if original == updated:
        return False
    backup = ini.with_suffix(".ini.bak")
    backup.write_text(original, encoding="utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=".nyverra-map-", suffix=".ini", dir=ini.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as fh:
            fh.write(updated)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, ini)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


if __name__ == "__main__":
    try:
        changed = configure(ROOT)
    except (ValueError, OSError) as exc:
        raise SystemExit(f"ERROR: {exc}")
    print("OK: TestWorld map configured" if changed else "OK: TestWorld already configured")
