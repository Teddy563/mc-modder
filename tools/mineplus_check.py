"""Fails if the toolkit links (github.com/<repo>) a known malware lure or ships a binary it shouldn't.

    python tools/check.py            # checks the modder/ folder this file lives in
    python tools/check.py <folder>   # checks a project made with /mineplus-new
"""
import sys
from pathlib import Path

# Suspected malware lures posing as mashup tools (research/rejected.json). Never link them.
LURES = (
    "TerminusBoulder/Universal-Game-Mashup-Studio",
    "TileTrackWarehouse/Passthrough-Mod-Forge",
    "StuccoWhisper/Extreme-Injector-V4",
)
# Game files, loaders and builds must come from their own sites at install time, never from the repo.
BINARIES = {".exe", ".dll", ".asi", ".sys", ".so", ".dylib", ".jar", ".zip", ".7z", ".rar", ".rpf", ".bsa", ".ba2", ".bdt"}
ALLOWED = {"gradle-wrapper.jar"}
TEXT = {".md", ".json", ".py", ".java", ".cpp", ".h", ".fx", ".sh", ".bat", ".gradle", ".properties", ".txt", ".toml", ".yml", ".yaml"}


def problems(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "build" in path.parts:
            continue
        if path.suffix.lower() in BINARIES and path.name not in ALLOWED:
            yield f"binary not allowed: {path.relative_to(root)}"
        if path.suffix.lower() in TEXT and path.name != Path(__file__).name:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for lure in LURES:
                if "github.com/" + lure.lower() in text:
                    yield f"malware lure linked in {path.relative_to(root)}: {lure}"


def _selftest(tmp: Path):
    (tmp / "a.md").write_text("see github.com/stuccowhisper/extreme-injector-v4", encoding="utf-8")
    (tmp / "ScriptHookV.dll").write_bytes(b"MZ")
    (tmp / "gradle-wrapper.jar").write_bytes(b"PK")
    found = list(problems(tmp))
    assert len(found) == 2, found


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as t:
        _selftest(Path(t))
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    found = list(problems(root))
    for p in found:
        print(p)
    print(f"{len(found)} problem(s) in {root}")
    sys.exit(1 if found else 0)
