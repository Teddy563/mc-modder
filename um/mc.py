"""Minecraft recon for agents: Java runtimes, launchers, instances, Loom caches. Read-only.

    um mc scan            # what's on this machine, plus warnings
    um mc scan --json     # machine-readable, for agents

Looks at PATH java, JAVA_HOME, common JDK folders, launcher-bundled runtimes, the official launcher's
.minecraft, Modrinth App (custom data folders too), Prism Launcher, CurseForge, and ~/.gradle. Never writes
to a launcher folder, opens the Modrinth DB read-only, and never reads account or auth files.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path

from um.common import text_utf8

HEAVY_MODS = 30          # a profile with this many mods is someone's play setup, not a dev sandbox
NEED_JDK = 25            # Minecraft 26.x targets Java 25
UNIX_JVM_DIRS = ["/usr/lib/jvm", "/Library/Java/JavaVirtualMachines"]


def _exe(name: str) -> str:
    return name + ".exe" if os.name == "nt" else name


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None


def _ini(p: Path) -> dict:
    """key=value lines of a Prism .cfg, sections ignored (missing file -> {})."""
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    return {k.strip(): v.strip() for k, _, v in (l.partition("=") for l in lines) if _ and not k.startswith(("[", "#", ";"))}


def _mods(game_dir: Path) -> int | None:
    d = game_dir / "mods"
    return sum(1 for f in d.iterdir() if f.suffix == ".jar") if d.is_dir() else None


# --------------------------------------------------------------------------- java

def _major(v: str) -> int | None:
    m = re.match(r"(?:1\.)?(\d+)", v or "")
    return int(m.group(1)) if m else None


def java_info(home: Path, source: str) -> dict | None:
    """A Java home (has bin/java): version from its `release` file, JDK if bin/javac exists."""
    home = Path(home)
    if not (home / "bin" / _exe("java")).is_file():
        return None
    rel = {}
    try:
        for line in (home / "release").read_text(encoding="utf-8", errors="replace").splitlines():
            k, _, v = line.partition("=")
            rel[k.strip()] = v.strip().strip('"')
    except OSError:
        pass
    ver = rel.get("JAVA_VERSION") or (re.search(r"(\d+(?:\.\d+)+)", home.name) or [None])[0] or (re.search(r"\d+", home.name) or [None])[0]
    jdk = (home / "bin" / _exe("javac")).is_file()
    return dict(path=str(home), version=ver, major=_major(ver or ""), kind="JDK" if jdk else "JRE",
                vendor=rel.get("IMPLEMENTOR"), source=source)


def _homes_under(root: Path, depth: int = 4):
    """Java homes at or below root (launcher runtimes nest them 3 deep)."""
    if not root.is_dir():
        return
    for dirpath, dirs, _ in os.walk(root):
        d = Path(dirpath)
        if (d / "bin" / _exe("java")).is_file():
            dirs[:] = []
            yield d
        elif len(d.relative_to(root).parts) >= depth:
            dirs[:] = []


def _path_java_home(env: dict) -> Path | None:
    exe = shutil.which("java", path=env.get("PATH", ""))
    if not exe:
        return None
    home = Path(exe).resolve().parent.parent
    if (home / "release").is_file():
        return home
    try:  # a shim (Oracle's javapath): ask the JVM where it lives
        r = subprocess.run([exe, "-XshowSettings:properties", "-version"], capture_output=True, timeout=15, **text_utf8())
        m = re.search(r"java\.home = (.+)", r.stderr + r.stdout)
        return Path(m.group(1).strip()) if m else home
    except (OSError, subprocess.TimeoutExpired):
        return home


def find_java(home: Path, env: dict, launcher_roots: list[tuple[Path, str]], extra_dirs=UNIX_JVM_DIRS) -> list[dict]:
    cands: list[tuple[Path, str]] = []
    p = _path_java_home(env)
    if p:
        cands.append((p, "PATH"))
    if env.get("JAVA_HOME"):
        cands.append((Path(env["JAVA_HOME"]), "JAVA_HOME"))
    for pf in {env.get("ProgramFiles"), env.get("ProgramW6432")} - {None}:
        for vendor in ("Eclipse Adoptium", "Java", "Microsoft", "Zulu", "BellSoft", "Amazon Corretto"):
            cands += [(h, vendor) for h in _homes_under(Path(pf) / vendor, 2)]
    for d, src in [(home / ".jdks", "~/.jdks"), (Path(env.get("GRADLE_USER_HOME") or home / ".gradle") / "jdks", "gradle toolchain"),
                   *[(Path(x), x) for x in extra_dirs]]:
        cands += [(h, src) for h in _homes_under(d, 3)]
    for d, src in launcher_roots:
        cands += [(h, src) for h in _homes_under(d)]
    out, seen = [], set()
    for h, src in cands:
        key = os.path.normcase(os.path.realpath(h))
        if key in seen:
            continue
        info = java_info(h, src)
        if info:
            seen.add(key)
            out.append(info)
        elif src == "JAVA_HOME":
            out.append(dict(path=str(h), version=None, major=None, kind="missing", vendor=None, source=src))
    return out


# --------------------------------------------------------------------------- launchers

def _loader_of(vid: str) -> str | None:
    v = vid.lower()
    for name in ("neoforge", "forge", "fabric", "quilt"):
        if name in v:
            return name
    return None


def official(mc: Path) -> dict | None:
    if not mc.is_dir():
        return None
    versions = []
    vroot = mc / "versions"
    for d in sorted(vroot.iterdir()) if vroot.is_dir() else []:
        if not d.is_dir():
            continue
        j = _read_json(d / f"{d.name}.json") or {}
        versions.append(dict(id=d.name, game=j.get("inheritsFrom") or j.get("id") or d.name, loader=_loader_of(d.name)))
    profiles = []
    # launcher_profiles.json: only the "profiles" key is read (old launchers kept auth data beside it)
    for p in ((_read_json(mc / "launcher_profiles.json") or {}).get("profiles") or {}).values():
        gd = Path(p["gameDir"]) if p.get("gameDir") else mc
        vid = p.get("lastVersionId") or ""
        game = next((v["game"] for v in versions if v["id"] == vid), vid)
        profiles.append(dict(name=p.get("name") or p.get("type") or vid, path=str(gd), minecraft=game,
                             loader=_loader_of(vid), loader_version=None, version_id=vid, mods=_mods(gd)))
    return dict(launcher="official", path=str(mc), versions=versions, instances=profiles)


def _modrinth_db(db: Path):
    """custom_dir, Java paths and instances from Modrinth App's app.db, opened read-only. Schemas vary by app version."""
    res = dict(custom_dir=None, java=[], rows={})
    if not db.is_file():
        return res
    try:
        con = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
    except sqlite3.Error:
        return res
    try:
        def q(sql):
            try:
                return con.execute(sql).fetchall()
            except sqlite3.Error:
                return []
        row = q("SELECT custom_dir FROM settings")
        res["custom_dir"] = row[0][0] if row and row[0][0] else None
        res["java"] = [r[0] for r in q("SELECT path FROM java_versions")]
        rows = q("SELECT i.path, i.name, s.game_version, s.loader, s.loader_version FROM instances i "
                 "LEFT JOIN instance_content_sets s ON s.id = i.applied_content_set_id") \
            or q("SELECT path, name, game_version, mod_loader, mod_loader_version FROM profiles")
        res["rows"] = {r[0]: r[1:] for r in rows}
    finally:
        con.close()
    return res


def modrinth(default_dirs: list[Path]) -> tuple[list[dict], list[tuple[Path, str]]]:
    found, runtimes, seen = [], [], set()
    for base in default_dirs:
        if not base.is_dir():
            continue
        info = _modrinth_db(base / "app.db")
        data = Path(info["custom_dir"]) if info["custom_dir"] else base
        key = os.path.normcase(str(data))
        if key in seen or not data.is_dir():
            continue
        seen.add(key)
        runtimes.append((data / "meta" / "java_versions", "Modrinth App"))
        runtimes += [(Path(j).parent.parent, "Modrinth App") for j in info["java"]]
        insts = []
        prof = data / "profiles"
        for d in sorted(prof.iterdir()) if prof.is_dir() else []:
            if not d.is_dir():
                continue
            name, game, loader, lver = info["rows"].get(d.name, (d.name, None, None, None))
            insts.append(dict(name=name, path=str(d), minecraft=game, loader=loader, loader_version=lver, mods=_mods(d)))
        found.append(dict(launcher="modrinth", path=str(data), config=str(base), instances=insts))
    return found, runtimes


_PRISM_LOADERS = {"net.fabricmc.fabric-loader": "fabric", "org.quiltmc.quilt-loader": "quilt",
                  "net.minecraftforge": "forge", "net.neoforged": "neoforge"}


def prism(data: Path) -> tuple[dict | None, list[tuple[Path, str]]]:
    if not data.is_dir():
        return None, []
    inst_dir = data / "instances"
    if _ini(data / "prismlauncher.cfg").get("InstanceDir"):
        inst_dir = data / _ini(data / "prismlauncher.cfg")["InstanceDir"]  # an absolute path replaces data
    insts = []
    for d in sorted(inst_dir.iterdir()) if inst_dir.is_dir() else []:
        if not (d / "instance.cfg").is_file():
            continue
        game = loader = lver = None
        for c in (_read_json(d / "mmc-pack.json") or {}).get("components", []):
            if c.get("uid") == "net.minecraft":
                game = c.get("version")
            elif c.get("uid") in _PRISM_LOADERS:
                loader, lver = _PRISM_LOADERS[c["uid"]], c.get("version")
        gd = next((d / s for s in (".minecraft", "minecraft") if (d / s).is_dir()), d / ".minecraft")
        insts.append(dict(name=_ini(d / "instance.cfg").get("name") or d.name, path=str(d), minecraft=game, loader=loader,
                          loader_version=lver, mods=_mods(gd)))
    return dict(launcher="prism", path=str(data), instances=insts), [(data / "java", "Prism Launcher")]


def curseforge(root: Path) -> dict | None:
    idir = root / "Instances"
    if not idir.is_dir():
        return None
    insts = []
    for d in sorted(idir.iterdir()):
        j = _read_json(d / "minecraftinstance.json")
        if j is None:
            continue
        bl = (j.get("baseModLoader") or {}).get("name") or ""  # e.g. "fabric-0.16.5-1.21.1", "forge-47.3.0"
        insts.append(dict(name=j.get("name") or d.name, path=str(d), minecraft=j.get("gameVersion"), loader=_loader_of(bl),
                          loader_version=bl.split("-")[1] if bl.count("-") else None, mods=_mods(d)))
    return dict(launcher="curseforge", path=str(root), instances=insts)


def loom_caches(gradle: Path) -> dict | None:
    d = gradle / "caches" / "fabric-loom"
    if not d.is_dir():
        return None
    vers = sorted(p.name for p in d.iterdir() if p.is_dir() and re.match(r"\d+\.\d+", p.name))
    return dict(path=str(d), minecraft_versions=vers)


# --------------------------------------------------------------------------- report

def scan(home: Path | None = None, env: dict | None = None, extra_jvm_dirs=UNIX_JVM_DIRS) -> dict:
    home = Path(home or Path.home())
    env = dict(os.environ if env is None else env)
    appdata = Path(env["APPDATA"]) if env.get("APPDATA") else None
    local = Path(env["LOCALAPPDATA"]) if env.get("LOCALAPPDATA") else None
    mac_sup = home / "Library" / "Application Support"
    xdg = Path(env.get("XDG_DATA_HOME") or home / ".local" / "share")

    launchers, runtimes = [], []
    for mc in [appdata / ".minecraft" if appdata else None, home / ".minecraft", mac_sup / "minecraft"]:
        o = official(mc) if mc else None
        if o and not any(x["path"] == o["path"] for x in launchers):
            launchers.append(o)
            runtimes.append((mc / "runtime", "official launcher"))
    if local:  # Microsoft Store / Xbox app launcher keeps its runtime here
        runtimes.append((local / "Packages" / "Microsoft.4297127D64EC6_8wekyb3d8bbwe" / "LocalCache" / "Local" / "runtime", "official launcher"))

    mr_dirs = [d for base in (appdata, xdg, mac_sup) if base for d in (base / "ModrinthApp", base / "com.modrinth.theseus")]
    mr, rt = modrinth(mr_dirs)
    launchers += mr
    runtimes += rt

    for data in [appdata / "PrismLauncher" if appdata else None, xdg / "PrismLauncher", mac_sup / "PrismLauncher"]:
        p, rt = prism(data) if data else (None, [])
        if p:
            launchers.append(p)
            runtimes += rt

    cf = curseforge(home / "curseforge" / "minecraft")
    if cf:
        launchers.append(cf)
        runtimes.append((home / "curseforge" / "minecraft" / "Install" / "runtime", "CurseForge"))

    java = find_java(home, env, runtimes, extra_jvm_dirs)
    loom = loom_caches(Path(env.get("GRADLE_USER_HOME") or home / ".gradle"))
    return dict(java=java, launchers=launchers, loom=loom, warnings=warnings(java, launchers))


def warnings(java: list[dict], launchers: list[dict]) -> list[str]:
    w = []
    jdks = [j for j in java if j["kind"] == "JDK" and (j["major"] or 0) >= NEED_JDK]
    if not jdks:
        jres = [j["path"] for j in java if j["kind"] == "JRE" and (j["major"] or 0) >= NEED_JDK]
        w.append(f"no JDK {NEED_JDK}+ found. Minecraft 26.x mods need a JDK {NEED_JDK} to build; JREs can't compile"
                 + (f" (Java {NEED_JDK} JRE only: {', '.join(jres)})" if jres else ""))
    jh = next((j for j in java if j["source"] == "JAVA_HOME"), None)
    if jh and jh["kind"] == "missing":
        w.append(f"JAVA_HOME points at {jh['path']}, which has no bin/java")
    elif jh and jdks and (jh["major"] or 0) < NEED_JDK:
        w.append(f"JAVA_HOME is Java {jh['major']}; point it (or a Gradle toolchain) at {jdks[0]['path']} for 26.x builds")
    if not launchers:
        w.append("no Minecraft launcher found (official, Modrinth App, Prism, CurseForge)")
    heavy = [f"{l['launcher']}:{Path(i['path']).name} ({i['mods']})" for l in launchers for i in l["instances"]
             if (i.get("mods") or 0) >= HEAVY_MODS]
    if heavy:
        w.append(f"{len(heavy)} instance(s) with {HEAVY_MODS}+ mods look like play profiles; give a bridge mod its own "
                 f"instance: {', '.join(heavy)}")
    return w


def format_report(r: dict) -> str:
    lines = ["java:"]
    for j in r["java"]:
        lines.append(f"  {j['kind']:7} {str(j['version'] or '?'):12} {j['path']}  ({j['source']})")
    if not r["java"]:
        lines.append("  none found")
    for l in r["launchers"]:
        lines.append(f"{l['launcher']}: {l['path']}")
        if l.get("versions"):
            lines.append("  versions: " + ", ".join(v["id"] for v in l["versions"]))
        for i in l["instances"]:
            ld = f"{i['loader']} {i.get('loader_version') or ''}".strip() if i.get("loader") else "vanilla"
            mods = "no mods/" if i["mods"] is None else f"{i['mods']} mods"
            lines.append(f"  {i['name']}  [{i['minecraft'] or '?'}, {ld}, {mods}]  {i['path']}")
    lo = r["loom"]
    lines.append(f"loom cache: {lo['path']}  ({', '.join(lo['minecraft_versions']) or 'no versions'})" if lo else "loom cache: none")
    for w in r["warnings"]:
        lines.append(f"WARNING: {w}")
    return "\n".join(lines)


def main(args):
    r = scan()
    print(json.dumps(r, indent=2) if args.json else format_report(r))


def register(sub):
    import argparse
    p = sub.add_parser("mc", help="Minecraft recon: Java runtimes, launchers, instances, Loom caches (read-only)",
                       description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cs = p.add_subparsers(dest="cmd", metavar="<cmd>")
    q = cs.add_parser("scan", help="report JDKs/JREs, launcher instances (version, loader, mod count), caches, warnings")
    q.add_argument("--json", action="store_true")
    q.set_defaults(func=main)
