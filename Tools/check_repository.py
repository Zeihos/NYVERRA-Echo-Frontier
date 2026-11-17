"""NYVERRA repository hygiene checks (Python 3.11+, no Unreal required).

Validates entry points, Markdown relative links and public repo safety hints.
This does NOT compile UE C++ or claim the project is gameplay-ready.
"""
from pathlib import Path
from urllib.parse import unquote
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md",
    "docs/README.md", "docs/STATUS.md", "docs/DEVELOPMENT.md",
)
REQUIRED_FILES = (
    "NYVERRA.uproject", "Source/NYVERRA/NYVERRA.Build.cs",
    "Source/NYVERRA/Private/NyGameMode.cpp",
    "Config/DefaultEngine.ini",
    "TEST_ALPHA_061_WINDOWS.bat",
    "Tools/test_alpha_061_offline.py",
    ".github/workflows/nyverra-offline.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
BAD_TRACKED_PREFIXES = ("Saved/", "Binaries/", "Intermediate/", "DerivedDataCache/")


def check_markdown_link(doc: Path, target: str) -> str | None:
    # External links and in-page anchors are not local paths.
    raw = unquote(target.strip().split(" ", 1)[0])
    raw = raw.split("#", 1)[0]
    if not raw or raw.startswith(("https://", "http://", "mailto:", "data:", "//")):
        return None
    if raw.startswith("/"):
        return f"{doc.relative_to(ROOT)}: absolute link not portable: {target}"
    destination = (doc.parent / raw).resolve()
    if not destination.is_relative_to(ROOT.resolve()):
        return f"{doc.relative_to(ROOT)}: link leaves repository: {target}"
    if not destination.exists():
        return f"{doc.relative_to(ROOT)}: broken relative link: {target}"
    return None


def run() -> int:
    errors = []
    for name in REQUIRED_FILES + DOCUMENTS:
        if not (ROOT / name).is_file():
            errors.append(f"Required project file missing: {name}")
    if errors:
        for error in errors:
            print("[ERROR]", error)
        return 1

    for name in DOCUMENTS:
        doc = ROOT / name
        text = doc.read_text(encoding="utf-8")
        # Ignore code fences so an example command does not count as a link.
        prose = re.sub(r"(?ms)^\s*`{3}[^\n]*\n.*?^\s*`{3}\s*$", "", text)
        for match in LINK_RE.finditer(prose):
            error = check_markdown_link(doc, match.group(1))
            if error:
                errors.append(error)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if len(readme) > 9000:
        errors.append("README.md is longer than the quick-entry limit (9000 chars)")
    if "Alpha 0.61" not in readme:
        errors.append("README.md must identify the current source version")
    if "не релиз" not in readme.lower():
        errors.append("README.md must state explicitly that the project is not a release")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for required in ("Saved/", "Binaries/", "Intermediate/", ".env"):
        if required not in gitignore:
            errors.append(f".gitignore missing critical exclusion: {required}")
    # Do not reject an unpacked source ZIP (it has no .git).
    git_index = ROOT / ".git" 
    if git_index.exists():
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            errors.append("git ls-files failed")
        else:
            paths = [b.decode("utf-8", errors="replace") for b in result.stdout.split(b"\0") if b]
            for tracked in paths:
                if tracked.startswith(BAD_TRACKED_PREFIXES):
                    errors.append(f"Generated runtime file is tracked: {tracked}")
                if tracked == ".env" or tracked.startswith(".env."):
                    errors.append(f"Potential secrets file is tracked: {tracked}")

    for error in errors:
        print("[ERROR]", error)
    if errors:
        print(f"[FAIL] {len(errors)} repository hygiene issue(s)")
        return 1
    print(f"[OK] Repository layout and {len(DOCUMENTS)} documentation entry points")
    print("[OK] Local Markdown links, safety ignores and current version")
    print("[NOTE] Does not run Unreal Engine or validate gameplay")
    return 0


if __name__ == "__main__":
    sys.exit(run())
