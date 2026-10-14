---
name: mc-merge
description: Bring another game's content, mechanics or rules into Minecraft as a Fabric mod, merge Minecraft with another mod or modpack, or convert real-world data into a Minecraft world. Use when the guest game doesn't need to run at all - "Halo's Warthog in Minecraft", "Bloons TD 6 inside Minecraft", "make this boss mod work with that one", "my city as a Minecraft map".
---

# Merging into Minecraft

The lighter direction: Minecraft is the only game running. Pick one of four patterns.

## 1. Content port
A weapon, mob, vehicle or block from another game, rebuilt as Minecraft content.
- Read the guest's real numbers (speed, damage, timers) from its files or a wiki, and write them into a
  table in `MODLOG.md` before coding.
- Assets: never copy the guest's files into the mod. Either a converter that runs on the user's own install
  and writes a private resource pack, or new lookalike art.
- The mod must still load with placeholder assets when the converted pack is missing.
- Write the content's JSON (recipes, loot tables, models, block states, tags, language) with Fabric's datagen, not
  by hand: datagen gets the folder names and JSON shapes right for the target version.
- Prior art: Halo 3 weapons, vehicles and maps in Minecraft
  (`knowledge/games/halo-3-mcc/halo-3-weapons-covenant-vehicles-and-maps-ported-into-minecr.md`); search for more
  with `um kb search minecraft`.

## 2. Headless rules inside Minecraft
For guests whose gameplay is numbers (tower defense, cards, puzzles, top-down 2D):
- Rewrite the guest's rules as a pure simulation that imports nothing from Minecraft, at the guest's own
  step rate and units.
- One function maps guest units to block coordinates, shared by server and client.
- Minecraft entities only for what the player touches; everything high-volume (projectiles, particles) is
  batched spawn records the client animates with the same motion code.
- Every UI button is a command, so each action can be tested without a screen.
- Oracle: run the sim headless first, then in Minecraft.
- Prior art: Bloons TD 6 inside Minecraft (`knowledge/games/minecraft/bloons-td-6-in-minecraft.md`).

## 3. Merge with another mod or modpack
- Pin exact versions of Minecraft, the loader and every mod in `MODLOG.md`.
- Integrate through the other mod's API or data (tags, recipes, data packs) before mixins into its code.
- If it's a Forge/NeoForge mod and you're on Fabric (or the reverse), port, don't wrap: the `port-a-mod` skill
  covers this, including a Forge 1.7.10 → Fabric 1.20.1 mapping table. Use the `minecraft-dev` MCP server's version
  diff to see what changed between the two Minecraft versions.
- Test inside the full pack headless (a dedicated server with every mod) before a client run:
  `knowledge/techniques/testing-a-fabric-mod-inside-a-large-modpack-headless.md`;
  `knowledge/games/minecraft/neoforge-26-2-modpack-audit-perf-mods.md` for a real pack audit.
- Ship only your mod and a list of the others with their official links. Never repack other people's jars.

## 4. World conversion (real world into Minecraft)
The RealWorldMC and Arnis direction: map data, elevation or photogrammetry turned into a world.
- Keep the converter separate from the data. Check each data source's licence (OpenStreetMap is ODbL and
  needs attribution) and write it into the world's README.
- 1 block = 1 metre unless the user picks another scale; record it.
- Prior art: RealWorldMC (github.com/Teddy563/realworldmc, Google 3D Tiles and Street View in a Fabric mod) and Arnis (github.com/louis-e/arnis, OpenStreetMap to Minecraft world).

## Starting and building a mod
- Start from Fabric's own starting point for the target version, not from the GTA passthrough template: clone
  `https://github.com/FabricMC/fabric-example-mod` at the branch named after the version (e.g. `26.2`), or use the
  web generator at https://fabricmc.net/develop/template/ (it can add datagen).
- Minecraft 26.x ships without obfuscation: Loom's non-remapping plugin `net.fabricmc.fabric-loom`, no `mappings`
  line, `implementation` and `jar` instead of `modImplementation` and `remapJar`, Mojang's class names, JDK 25
  (`um mc scan` shows which Java on the machine is a JDK). `python tools/mc_check.py --stale <project>` catches the
  pre-26 forms models tend to write.
- Look up every class, method and mixin target with the `minecraft-dev` MCP server before using it; never guess
  a name from memory of another version.
- Run: `./gradlew runClient` (dev client, logs in `run/logs/latest.log`), `./gradlew build` for the jar. Install
  the jar only into a dedicated profile.
- Versions: `docs/VERSIONS.md` has the Minecraft → Java → Fabric Loader → Fabric API → Loom table and how to
  refresh it.

## Testing
- One server GameTest per ported mechanic (Fabric's test API, `src/gametest/`): the guest's numbers from
  `MODLOG.md` as assertions. See `knowledge/techniques/fabric-1-20-1-gametests-as-the-oracle-of-a-large-mod-port.md`.
- A client game test with a screenshot for anything visual (models, textures: a missing texture shows as purple).
- In CI, boot the built jar, not just the dev run:
  [headlesshq/mc-runtime-test](https://github.com/headlesshq/mc-runtime-test) (MIT) starts a real client from the
  jar and runs the GameTests.
- Agent play-testing: [denfry/mcpfabric](https://github.com/denfry/mcpfabric) (MIT) gives an agent screenshots,
  commands and movement inside a running client over MCP. It has operator-level control: dev profile only, bound to
  localhost with its token, never shipped in a release or a modpack.

## Done means
- It loads in a clean profile with only its declared dependencies.
- Every ported mechanic has a GameTest that asserts the guest's numbers from `MODLOG.md`, and the tests pass.
- No guest or Minecraft assets in the repo (`python tools/mc_check.py <project>`); credits for every source.
