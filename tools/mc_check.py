"""MC Modder's guard for a toolkit or project folder.

    python tools/mc_check.py [folder]           # malware-lure links and files that must never be committed
    python tools/mc_check.py --stale [folder]   # pre-26 Minecraft code that won't build on 26.x

The first check fails on links to known malware lures posing as mashup tools, and on binaries: game files,
loaders and builds come from their own sites at install time, never from a repo. The second check is for 26.x
projects (no mappings, Mojang names): it flags the Loom setup and Yarn names that models carry over from
1.21.x and older. With no folder, the toolkit itself is checked.
"""
import re
import sys
from pathlib import Path

# Suspected malware lures posing as mashup tools. Never link them.
LURES = (
    "TerminusBoulder/Universal-Game-Mashup-Studio",
    "TileTrackWarehouse/Passthrough-Mod-Forge",
    "StuccoWhisper/Extreme-Injector-V4",
)
LURE_HOSTS = ("github.com/", "raw.githubusercontent.com/", "codeload.github.com/", "api.github.com/repos/")
BINARIES = {
    ".exe", ".dll", ".asi", ".sys", ".so", ".dylib", ".jar", ".class", ".pdb", ".zip", ".7z", ".rar",
    ".rpf", ".bsa", ".ba2", ".bdt", ".pak", ".esp", ".esm", ".esl", ".mca", ".mrpack",
}
TEXT = {
    ".md", ".json", ".py", ".java", ".kt", ".kts", ".cpp", ".c", ".h", ".hpp", ".cs", ".rs", ".fx", ".hlsl",
    ".sh", ".bat", ".cmd", ".ps1", ".gradle", ".properties", ".txt", ".toml", ".yml", ".yaml", ".ts", ".js",
    ".mjs", ".lua", ".html", ".cfg", ".ini",
}
SKIP_DIRS = {".git", "build", ".gradle", "run", "node_modules", "__pycache__", ".venv", ".pytest_cache"}

# (pattern, why) for 26.x projects, checked in build scripts and Java/Kotlin sources.
STALE = (
    (r"""id\s*\(?\s*['"]fabric-loom['"]""", "old remapping Loom plugin: 26.x uses 'net.fabricmc.fabric-loom'"),
    (r"^\s*mappings[\s(]", "a mappings line: 26.x ships unobfuscated, drop it"),
    (r"\bmod(Implementation|CompileOnly|RuntimeOnly|Api)\b", "mod* configuration: use implementation/compileOnly/runtimeOnly on 26.x"),
    (r"\bremapJar\b", "remapJar: 26.x builds a plain jar (task 'jar')"),
    (r"JavaVersion\.VERSION_(1[0-9]|2[0-4])\b|\brelease\s*=\s*(1[0-9]|2[0-4])\b|JavaLanguageVersion\.of\((1[0-9]|2[0-4])\)",
     "Java older than 25: 26.x needs Java 25"),
    (r"\b(MinecraftClient|ClientPlayerEntity|ServerPlayerEntity|PlayerEntity|ClientWorld|ServerWorld|MatrixStack|DrawContext|TextRenderer)\b",
     "Yarn class name: 26.x uses Mojang names (Minecraft, LocalPlayer, ServerPlayer, Player, ClientLevel, ServerLevel, PoseStack, GuiGraphics, Font)"),
)
STALE_FILES = {".gradle", ".kts", ".java", ".kt"}


def files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(root).parts):
            yield path


def problems(root: Path):
    me = Path(__file__).resolve()
    for path in files(root):
        rel = path.relative_to(root)
        ext = path.suffix.lower()
        wrapper = path.name == "gradle-wrapper.jar" and rel.parent.as_posix().endswith("gradle/wrapper")
        if ext in BINARIES and not wrapper:
            yield f"binary not allowed: {rel}"
        if ext in TEXT and path.resolve() != me:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for lure in LURES:
                if any(host + lure.lower() in text for host in LURE_HOSTS):
                    yield f"malware lure linked in {rel}: {lure}"


def stale(root: Path):
    for path in files(root):
        if path.suffix.lower() not in STALE_FILES:
            continue
        rel = path.relative_to(root)
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if line.lstrip().startswith(("//", "*", "/*")):
                continue
            for pattern, why in STALE:
                if re.search(pattern, line):
                    yield f"{rel}:{n}: {why}"


def main(argv):
    check = stale if "--stale" in argv else problems
    args = [a for a in argv if a != "--stale"]
    root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
    found = list(check(root))
    for p in found:
        print(p)
    print(f"{len(found)} problem(s) in {root}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
