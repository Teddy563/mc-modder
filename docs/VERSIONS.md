# Minecraft version matrix

Checked 2026-10-15 against Fabric Meta and Fabric's Maven. Versions move every few weeks: refresh before
pinning anything (commands below), and write the versions you used into `MODLOG.md`.

| Minecraft | Java to build | Fabric Loader | Fabric API (latest) | Mappings | Loom plugin |
|---|---|---|---|---|---|
| 26.3 | JDK 25 | 0.19.5 | 0.163.0+26.3 | none (unobfuscated) | `net.fabricmc.fabric-loom` |
| 26.2 | JDK 25 | 0.19.5 | 0.161.0+26.2 | none | `net.fabricmc.fabric-loom` |
| 26.1.2 | JDK 25 | 0.19.5 | 0.155.3+26.1.2 | none | `net.fabricmc.fabric-loom` |
| 1.21.11 | JDK 21 | 0.19.5 | 0.141.6+1.21.11 | Yarn or Mojang (last version with Yarn) | `fabric-loom` (remapping) |
| 1.21.1 | JDK 21 | 0.19.5 | 0.116.17+1.21.1 | Yarn or Mojang | `fabric-loom` (remapping) |
| 1.20.1 | JDK 17 | 0.19.5 | see Maven | Yarn or Mojang | `fabric-loom` (remapping) |

- **26.x vs 1.21.x is the big split.** 26.x has no mappings, `implementation`/`jar` instead of
  `modImplementation`/`remapJar`, and Mojang class names everywhere. Code or build scripts from 1.21.x and older
  don't build on 26.x; `python tools/mc_check.py --stale <project>` flags the usual leftovers.
- **Loom:** 26.x needs the 1.18+ line (the GTA V template uses `1.18-SNAPSHOT`; `1.19.0-alpha.7` is the newest
  published). Gradle 9.x (the template's wrapper is 9.7.1).
- **The template's pins** (`examples/minecraft-gta5-passthrough/mc/gradle.properties`) are what its author
  tested; bump them only together with a passing build and GameTests.
- **Runtimes:** launchers bundle JREs (the official launcher's `runtime/`, Modrinth App's `meta/java_versions`).
  They run the game but can't compile a mod. `um mc scan` lists every Java and says which are JDKs.

## Refreshing this table
```bash
curl -s https://meta.fabricmc.net/v2/versions/game          # Minecraft versions Fabric supports
curl -s https://meta.fabricmc.net/v2/versions/loader        # Fabric Loader versions
curl -s https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml   # Fabric API, suffix +<mc>
curl -s https://maven.fabricmc.net/net/fabricmc/fabric-loom/net.fabricmc.fabric-loom.gradle.plugin/maven-metadata.xml
```
Java per Minecraft version: the `javaVersion.majorVersion` field of that version's JSON in Mojang's manifest
(`https://piston-meta.mojang.com/mc/game/version_manifest_v2.json`).
