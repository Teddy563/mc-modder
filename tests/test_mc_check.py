"""MC Modder's Minecraft layer: tools/mc_check.py, and that the skills only point at files that exist."""
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mc_check", ROOT / "tools" / "mc_check.py")
mc_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mc_check)

LAYER = [ROOT / "skills" / s / "SKILL.md" for s in ("mc-modder", "minecraft-bridge", "host-adapters", "mc-merge")]
# Files the skills tell an agent to create in its own project, not in this repo.
PROJECT_FILES = {"docs/CONTRACT.md"}
LAYER += [ROOT / "skills" / "mc-modder" / "references" / "safety.md", ROOT / "commands" / "mc-new.md"]


def test_lures_and_binaries(tmp_path):
    # Built by concatenation so this file itself never contains a lure link.
    gh, raw = "https://github.com/", "https://raw.githubusercontent.com/"
    (tmp_path / "a.md").write_text("see " + gh + "stuccowhisper/extreme-injector-v4", encoding="utf-8")
    (tmp_path / "b.ps1").write_text("iwr " + raw + "TileTrackWarehouse/Passthrough-Mod-Forge/main/x", encoding="utf-8")
    (tmp_path / "c.md").write_text("Never use TerminusBoulder/Universal-Game-Mashup-Studio.", encoding="utf-8")  # named, not linked
    (tmp_path / "ScriptHookV.dll").write_bytes(b"MZ")
    (tmp_path / "gradle-wrapper.jar").write_bytes(b"PK")                     # not under gradle/wrapper: flagged
    (tmp_path / "gradle" / "wrapper").mkdir(parents=True)
    (tmp_path / "gradle" / "wrapper" / "gradle-wrapper.jar").write_bytes(b"PK")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "mod.jar").write_bytes(b"PK")                       # build output is ignored
    found = sorted(mc_check.problems(tmp_path))
    assert found == sorted([
        "malware lure linked in a.md: StuccoWhisper/Extreme-Injector-V4",
        "malware lure linked in b.ps1: TileTrackWarehouse/Passthrough-Mod-Forge",
        "binary not allowed: ScriptHookV.dll",
        "binary not allowed: gradle-wrapper.jar",
    ]), found


def test_stale_pre26_code(tmp_path):
    (tmp_path / "build.gradle").write_text(
        "plugins { id 'fabric-loom' version '1.10' }\n"
        "dependencies {\n  mappings \"net.fabricmc:yarn:1.21.1+build.3:v2\"\n  modImplementation \"x\"\n}\n"
        "java { sourceCompatibility = JavaVersion.VERSION_21 }\nremapJar { }\n", encoding="utf-8")
    (tmp_path / "A.java").write_text("// MinecraftClient in a comment is fine\nclass A { MinecraftClient c; }\n", encoding="utf-8")
    found = list(mc_check.stale(tmp_path))
    assert len(found) == 6, found
    assert any(f.startswith("A.java:2:") for f in found)

    good = tmp_path / "good"
    good.mkdir()
    (good / "build.gradle").write_text(
        "plugins { id 'net.fabricmc.fabric-loom' version '1.18-SNAPSHOT' }\n"
        "dependencies { implementation \"x\" }\njava { sourceCompatibility = JavaVersion.VERSION_25 }\n", encoding="utf-8")
    (good / "B.java").write_text("import net.minecraft.client.Minecraft;\nclass B { Minecraft m; }\n", encoding="utf-8")
    assert list(mc_check.stale(good)) == []


def test_toolkit_is_clean():
    assert list(mc_check.problems(ROOT)) == []
    assert list(mc_check.stale(ROOT / "examples" / "minecraft-gta5-passthrough" / "mc")) == []


def test_layer_paths_exist():
    # Every repo path the Minecraft skills and /mc-new mention in backticks must exist.
    prefixes = ("knowledge/", "skills/", "examples/", "docs/", "tools/", "commands/", ".github/")
    missing = []
    for doc in LAYER:
        for ref in re.findall(r"`([^`\s]+)`", doc.read_text(encoding="utf-8")):
            ref = ref.rstrip(".,;:)")
            if not ref.startswith(prefixes) or "<" in ref or "*" in ref or ref in PROJECT_FILES:
                continue
            if not (ROOT / ref).exists():
                missing.append(f"{doc.relative_to(ROOT).as_posix()}: {ref}")
    assert not missing, missing


def test_command_copies_match():
    # Claude Code loads commands/ from the plugin and .claude/commands/ from a clone.
    assert (ROOT / ".claude" / "commands" / "mc-new.md").read_bytes() == (ROOT / "commands" / "mc-new.md").read_bytes()
