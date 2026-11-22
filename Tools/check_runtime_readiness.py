"""NYVERRA readiness report: source/build checks are NOT playable-map checks.

Run from any directory: python Tools/check_runtime_readiness.py [--strict].
Exit 0 in report mode. Strict mode fails if the saved map or map configuration
is missing. No Unreal Editor installation is needed for this diagnostic.
"""
from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION = "/Script/EngineSettings.GameMapsSettings"
MAP_KEYS = ("GameDefaultMap", "EditorStartupMap", "ServerDefaultMap")


def inspect(root: Path) -> list[str]:
    problems: list[str] = []
    project = root / "NYVERRA.uproject"
    try:
        metadata = json.loads(project.read_text(encoding="utf-8-sig"))
        if metadata.get("EngineAssociation") != "5.8":
            problems.append("Unreal version must be 5.8")
        if not any(m.get("Name") == "NYVERRA" for m in metadata.get("Modules", [])):
            problems.append("NYVERRA runtime module missing from project")
    except (OSError, ValueError, TypeError) as exc:
        problems.append(f"Cannot read Unreal project: {exc}")

    ini = configparser.ConfigParser(interpolation=None, strict=False)
    ini.optionxform = str
    try:
        with (root / "Config/DefaultEngine.ini").open(encoding="utf-8-sig") as fh:
            ini.read_file(fh)
    except (OSError, configparser.Error) as exc:
        problems.append(f"Cannot read DefaultEngine.ini: {exc}")
        return problems

    if not ini.has_section(SECTION):
        problems.append("GameMapsSettings section is missing")
        return problems

    for key in MAP_KEYS:
        value = ini.get(SECTION, key, fallback="").strip().split(".", 1)[0]
        if not value:
            problems.append(f"{key} is not configured")
        elif not value.startswith("/Game/"):
            problems.append(f"{key} points to {value}, not a packaged project map")
        else:
            relative = value[len("/Game/"):]
            if ".." in Path(relative).parts or not relative:
                problems.append(f"{key} has an unsafe map path")
            elif not (root / "Content" / (relative + ".umap")).is_file():
                problems.append(f"{key} points to absent Content/{relative}.umap")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="NYVERRA map readiness")
    parser.add_argument("--strict", action="store_true",
                        help="fail if runtime readiness is not met")
    args = parser.parse_args()
    problems = inspect(ROOT)
    if problems:
        print("[NOT READY] Playable map configuration:")
        for issue in problems:
            print("  -", issue)
        print("[NEXT] Build UE5.8, create and verify TestWorld.umap in Unreal Editor,")
        print("       commit the saved map and its required assets, update map settings.")
        print("[NOTE] This tool does not compile C++ or test network gameplay.")
        return 1 if args.strict else 0
    print("[MAP READY] Configured map files exist in Content; gameplay still unverified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
