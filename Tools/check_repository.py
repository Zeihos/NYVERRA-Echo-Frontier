"""Checks the public NYVERRA GitHub layout without Unreal Engine.

Checks relevant links in Russian documentation, source entry points, brand SVG
structure and common accidental public disclosures. No network or dependencies.
This is not a C++ compilation or gameplay test.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
    "docs/README.md", "docs/STATUS.md", "docs/DEVELOPMENT.md",
    "docs/ROADMAP.md", "docs/REPOSITORY_PROFILE.md",
    "docs/archive/README.md", "docs/archive/legacy/README.md",
    "assets/brand/README.md",
)
REQUIRED = (
    "NYVERRA.uproject", "Source/NYVERRA/NYVERRA.Build.cs",
    "Source/NYVERRA/Private/NyGameMode.cpp", "Config/DefaultEngine.ini",
    "CHECK_PROJECT_WINDOWS.bat", "TEST_ALPHA_063_WINDOWS.bat",
    "Tools/test_alpha_063_offline.py", "Tools/check_repository.py",
    ".github/workflows/nyverra-offline.yml", ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "assets/brand/nyverra-cover.svg", "assets/brand/nyverra-mark.svg",
)
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HTML_ASSET = re.compile(r"<(?:img|a)\b[^>]*?\b(?:src|href)=[\"']([^\"']+)[\"']", re.I)
FENCE = re.compile(r"(?ms)^[ \t]*`{3}[^\n]*\n.*?^[ \t]*`{3}[ \t]*$")
LEGACY_ROOT = re.compile(r"^(?:ALPHA_0\d\d[^/]*\.txt|TESTING_0\d\d\.txt|PUSH_TO_GITHUB_PRIVATE[^/]*\.bat|PUSH_NYVERRA_RESUME_MAIN\.bat)$")
BUILD_PREFIXES = ("Saved/", "Binaries/", "Intermediate/", "DerivedDataCache/")
PRIVATE_FILE = re.compile(r"(^|/)(?:\.env(?:\..+)?|[^/]+\.(?:pem|key|p12|pfx|sav))$", re.I)


def resolve_link(document: Path, target: str) -> str | None:
    """Return an error for a missing local Markdown or HTML link."""
    cleaned = unquote(target.strip().split(" ", 1)[0]).split("#", 1)[0]
    cleaned = cleaned.split("?", 1)[0]
    if not cleaned or cleaned.startswith(("http://", "https://", "mailto:", "data:", "//")):
        return None
    if cleaned.startswith("/"):
        return f"{document.relative_to(ROOT)}: absolute link {target}"
    path = (document.parent / cleaned).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        return f"{document.relative_to(ROOT)}: path escapes repository {target}"
    if not path.exists():
        return f"{document.relative_to(ROOT)}: broken link {target}"
    return None


def verify_svg(filename: Path) -> list[str]:
    """SVG must be local XML with a real SVG root; no remote fetches."""
    try:
        parsed = ET.parse(filename)
        tag = parsed.getroot().tag
        if tag != "{http://www.w3.org/2000/svg}svg":
            return [f"{filename.relative_to(ROOT)}: not an SVG root element"]
        return []
    except ET.ParseError as exc:
        return [f"{filename.relative_to(ROOT)}: invalid SVG XML: {exc}"]


def run() -> int:
    issues: list[str] = []
    for filename in (*DOCS, *REQUIRED):
        if not (ROOT / filename).is_file():
            issues.append(f"Missing required file: {filename}")
    if issues:
        for issue in issues:
            print("[ERROR]", issue)
        return 1

    # Check links in ALL up-to-date docs, not historical .txt notes.
    for filename in DOCS:
        doc = ROOT / filename
        body = FENCE.sub("", doc.read_text(encoding="utf-8"))
        targets = [m.group(1) for m in LINK.finditer(body)]
        targets += [m.group(1) for m in HTML_ASSET.finditer(body)]
        for target in targets:
            if problem := resolve_link(doc, target):
                issues.append(problem)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if len(readme) > 12000:
        issues.append("README is too long for a useful project entry point")
    if "Alpha 0.63" not in readme or "не релиз" not in readme.lower():
        issues.append("README must show current alpha and unreleased status")
    if "assets/brand/nyverra-cover.svg" not in readme:
        issues.append("README lost the project branding header")

    project = json.loads((ROOT / "NYVERRA.uproject").read_text(encoding="utf-8"))
    if project.get("EngineAssociation") != "5.8":
        issues.append("Unexpected Unreal EngineAssociation (expected 5.8)")
    for svg in ("assets/brand/nyverra-cover.svg", "assets/brand/nyverra-mark.svg"):
        issues.extend(verify_svg(ROOT / svg))

    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for item in (*BUILD_PREFIXES, ".env"):
        if item not in ignored:
            issues.append(f".gitignore missing safety rule: {item}")

    # Use Git index when available; source ZIP users can still run these checks.
    if (ROOT / ".git").exists():
        p = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                           capture_output=True, check=False)
        if p.returncode != 0:
            issues.append("git ls-files failed")
        else:
            names = [item.decode("utf-8", "replace") for item in p.stdout.split(b"\0") if item]
            for name in names:
                if name.startswith(BUILD_PREFIXES) or PRIVATE_FILE.search(name):
                    issues.append(f"Potential generated/private file tracked: {name}")
                if "/" not in name and LEGACY_ROOT.match(name):
                    issues.append(f"Archive obsolete root file: {name}")

    for issue in issues:
        print("[ERROR]", issue)
    if issues:
        print(f"[FAIL] {len(issues)} repository issue(s)")
        return 1
    print(f"[OK] {len(DOCS)} documentation files and their local links")
    print("[OK] Unreal project metadata and both SVG branding assets")
    print("[OK] Public repository hygiene, source files and Git ignore rules")
    print("[NOTE] Unreal Engine C++ and network runtime were NOT tested")
    return 0


if __name__ == "__main__":
    sys.exit(run())
