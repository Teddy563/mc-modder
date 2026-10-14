"""Offline tests for `um mc scan`: fake launcher trees and Java homes in tmp_path, no real PC paths."""
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from um import mc  # noqa: E402

EXE = ".exe" if os.name == "nt" else ""


def make(root: Path, files: dict):
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def java_home(root: Path, version: str, jdk: bool):
    files = {f"bin/java{EXE}": "", "release": f'IMPLEMENTOR="Test"\nJAVA_VERSION="{version}"\n'}
    if jdk:
        files[f"bin/javac{EXE}"] = ""
    make(root, files)


def mods(d: Path, n: int):
    make(d, {f"mods/m{i}.jar": "" for i in range(n)} | {"mods/off.jar.disabled": ""})


def fake_env(tmp_path):
    home, appdata, pf = tmp_path / "home", tmp_path / "AppData" / "Roaming", tmp_path / "PF"
    return home, dict(APPDATA=str(appdata), LOCALAPPDATA=str(tmp_path / "AppData" / "Local"), ProgramFiles=str(pf), PATH="")


def run_scan(tmp_path, env_extra=None):
    home, env = fake_env(tmp_path)
    env.update(env_extra or {})
    return mc.scan(home=home, env=env, extra_jvm_dirs=[])


def test_java_kinds_versions_and_jdk25_warning(tmp_path):
    pf = tmp_path / "PF"
    java_home(pf / "Eclipse Adoptium" / "jdk-21.0.5", "21.0.5", jdk=True)
    java_home(pf / "Java" / "jre1.8.0_481", "1.8.0_481", jdk=False)
    java_home(tmp_path / "home" / ".gradle" / "jdks" / "jdk-17", "17.0.2", jdk=True)
    java_home(tmp_path / "AppData/Roaming/.minecraft/runtime/java-runtime-epsilon/windows-x64/java-runtime-epsilon", "25.0.1", jdk=False)
    (tmp_path / "AppData/Roaming/.minecraft/versions").mkdir(parents=True)
    r = run_scan(tmp_path, {"JAVA_HOME": str(pf / "Eclipse Adoptium" / "jdk-21.0.5")})
    by = {Path(j["path"]).name: j for j in r["java"]}
    assert by["jdk-21.0.5"]["kind"] == "JDK" and by["jdk-21.0.5"]["major"] == 21 and by["jdk-21.0.5"]["source"] == "JAVA_HOME"
    assert by["jre1.8.0_481"]["kind"] == "JRE" and by["jre1.8.0_481"]["major"] == 8
    assert by["jdk-17"]["source"] == "gradle toolchain"
    assert by["java-runtime-epsilon"]["major"] == 25 and by["java-runtime-epsilon"]["source"] == "official launcher"
    assert len(r["java"]) == 4  # JAVA_HOME and the Program Files hit are deduplicated
    w = " ".join(r["warnings"])
    assert "need a JDK 25" in w and "JREs can't compile" in w and "java-runtime-epsilon" in w


def test_jdk25_present_no_warning_but_java_home_hint(tmp_path):
    java_home(tmp_path / "home" / ".jdks" / "temurin-25", "25.0.1", jdk=True)
    java_home(tmp_path / "PF" / "Java" / "jdk-21", "21.0.9", jdk=True)
    r = run_scan(tmp_path, {"JAVA_HOME": str(tmp_path / "PF" / "Java" / "jdk-21")})
    w = " ".join(r["warnings"])
    assert "need a JDK 25" not in w
    assert "JAVA_HOME is Java 21" in w and "temurin-25" in w


def test_missing_java_home(tmp_path):
    r = run_scan(tmp_path, {"JAVA_HOME": str(tmp_path / "nope")})
    assert any("has no bin/java" in w for w in r["warnings"])
    assert any("no Minecraft launcher" in w for w in r["warnings"])


def test_official_launcher(tmp_path):
    mcd = tmp_path / "AppData/Roaming/.minecraft"
    make(mcd, {
        "versions/1.21.1/1.21.1.json": {"id": "1.21.1"},
        "versions/fabric-loader-0.16.5-1.21.1/fabric-loader-0.16.5-1.21.1.json": {"id": "fabric-loader-0.16.5-1.21.1", "inheritsFrom": "1.21.1"},
        "versions/version_manifest_v2.json": {},
        "launcher_profiles.json": {"profiles": {
            "a": {"name": "Fabric dev", "lastVersionId": "fabric-loader-0.16.5-1.21.1", "gameDir": str(tmp_path / "devgame")},
            "b": {"type": "latest-release", "lastVersionId": "latest-release"}},
            "authenticationDatabase": {"x": {"accessToken": "SECRET"}}},
        "launcher_accounts.json": {"accounts": {"x": {"accessToken": "SECRET"}}},
    })
    mods(tmp_path / "devgame", 3)
    r = run_scan(tmp_path)
    o = next(l for l in r["launchers"] if l["launcher"] == "official")
    assert [v["id"] for v in o["versions"]] == ["1.21.1", "fabric-loader-0.16.5-1.21.1"]
    assert o["versions"][1] == {"id": "fabric-loader-0.16.5-1.21.1", "game": "1.21.1", "loader": "fabric"}
    dev = next(i for i in o["instances"] if i["name"] == "Fabric dev")
    assert dev["minecraft"] == "1.21.1" and dev["loader"] == "fabric" and dev["mods"] == 3
    assert next(i for i in o["instances"] if i["name"] == "latest-release")["path"] == str(mcd)
    out = json.dumps(r) + mc.format_report(r)
    assert "SECRET" not in out


def _modrinth_db(path: Path, custom_dir):
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE settings (id INTEGER, custom_dir TEXT);
        CREATE TABLE java_versions (major_version INTEGER, full_version TEXT, architecture TEXT, path TEXT);
        CREATE TABLE instances (id TEXT, path TEXT, applied_content_set_id TEXT, name TEXT);
        CREATE TABLE instance_content_sets (id TEXT, game_version TEXT, loader TEXT, loader_version TEXT);
        CREATE TABLE minecraft_users (uuid TEXT, username TEXT, access_token TEXT);
    """)
    con.execute("INSERT INTO settings VALUES (0, ?)", (custom_dir,))
    con.execute("INSERT INTO instances VALUES ('i1', 'Dev Box', 'c1', 'Bridge Dev')")
    con.execute("INSERT INTO instance_content_sets VALUES ('c1', '26.2', 'fabric', '0.19.5')")
    con.execute("INSERT INTO minecraft_users VALUES ('u', 'player', 'SECRET')")
    con.commit()
    con.close()


def test_modrinth_relocated_data_dir(tmp_path):
    cfg = tmp_path / "AppData/Roaming/ModrinthApp"
    data = tmp_path / "Elsewhere" / "ModrinthApp"
    cfg.mkdir(parents=True)
    _modrinth_db(cfg / "app.db", str(data))
    mods(data / "profiles" / "Dev Box", 2)
    mods(data / "profiles" / "Big Pack", 40)
    java_home(data / "meta" / "java_versions" / "zulu25.34.17-ca-jre25.0.3-win_x64", "25.0.3", jdk=False)
    before = (cfg / "app.db").stat().st_mtime_ns
    r = run_scan(tmp_path)
    m = next(l for l in r["launchers"] if l["launcher"] == "modrinth")
    assert m["path"] == str(data)
    dev = next(i for i in m["instances"] if i["path"].endswith("Dev Box"))
    assert (dev["name"], dev["minecraft"], dev["loader"], dev["loader_version"], dev["mods"]) == ("Bridge Dev", "26.2", "fabric", "0.19.5", 2)
    big = next(i for i in m["instances"] if i["path"].endswith("Big Pack"))
    assert big["name"] == "Big Pack" and big["minecraft"] is None and big["mods"] == 40
    assert any(j["source"] == "Modrinth App" and j["kind"] == "JRE" and j["major"] == 25 for j in r["java"])
    assert any("Big Pack (40)" in w and "own instance" in w for w in r["warnings"])
    assert not any("Dev Box" in w for w in r["warnings"])
    assert "SECRET" not in json.dumps(r)
    assert (cfg / "app.db").stat().st_mtime_ns == before
    assert not (cfg / "profiles").exists()


def test_modrinth_default_dir_without_db(tmp_path):
    mods(tmp_path / "AppData/Roaming/ModrinthApp/profiles/Plain", 1)
    m = next(l for l in run_scan(tmp_path)["launchers"] if l["launcher"] == "modrinth")
    assert m["instances"][0]["name"] == "Plain" and m["instances"][0]["mods"] == 1


def test_prism_instance(tmp_path):
    pr = tmp_path / "AppData/Roaming/PrismLauncher"
    make(pr, {
        "prismlauncher.cfg": "[General]\nInstanceDir=instances\n",
        "instances/Bridge/instance.cfg": "[General]\nname=Bridge Test\nInstanceType=OneSix\n",
        "instances/Bridge/mmc-pack.json": {"components": [
            {"uid": "org.lwjgl3", "version": "3.3.3"},
            {"uid": "net.minecraft", "version": "1.21.1"},
            {"uid": "net.neoforged", "version": "21.1.77"}]},
        "instances/_LAUNCHER_TEMP/readme.txt": "",
    })
    mods(pr / "instances/Bridge/minecraft", 5)
    java_home(pr / "java" / "java-runtime-delta", "21.0.7", jdk=True)
    r = run_scan(tmp_path)
    p = next(l for l in r["launchers"] if l["launcher"] == "prism")
    assert p["instances"] == [dict(name="Bridge Test", path=str(pr / "instances/Bridge"), minecraft="1.21.1",
                                   loader="neoforge", loader_version="21.1.77", mods=5)]
    assert any(j["source"] == "Prism Launcher" for j in r["java"])


def test_curseforge_and_loom(tmp_path):
    cf = tmp_path / "home/curseforge/minecraft/Instances/All the Mods"
    make(cf, {"minecraftinstance.json": {"name": "All the Mods", "gameVersion": "1.20.1",
                                         "baseModLoader": {"name": "forge-47.3.0"}}})
    mods(cf, 31)
    make(tmp_path / "home/.gradle/caches/fabric-loom", {"1.21.1/minecraft-client.jar": "", "26.2/x": "", "assets/x": ""})
    r = run_scan(tmp_path)
    c = next(l for l in r["launchers"] if l["launcher"] == "curseforge")
    assert c["instances"][0] | {} == dict(name="All the Mods", path=str(cf), minecraft="1.20.1", loader="forge",
                                          loader_version="47.3.0", mods=31)
    assert r["loom"]["minecraft_versions"] == ["1.21.1", "26.2"]
    text = mc.format_report(r)
    assert "All the Mods  [1.20.1, forge 47.3.0, 31 mods]" in text and "loom cache:" in text


def test_cli_registers_mc_scan():
    import argparse
    ap = argparse.ArgumentParser()
    mc.register(ap.add_subparsers(dest="group"))
    a = ap.parse_args(["mc", "scan", "--json"])
    assert a.json and a.func is mc.main
