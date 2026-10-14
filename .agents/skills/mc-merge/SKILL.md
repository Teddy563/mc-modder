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
- Prior art: the Halo 3 Warthog and World at War ports in `knowledge/` (`um kb search halo`).

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
- If it's a Forge/NeoForge mod and you're on Fabric (or the reverse), port, don't wrap: the `port-a-mod` skill covers this, including a Forge 1.7.10 → Fabric 1.20.1 mapping table.
- Test inside the full pack headless (a dedicated server with every mod) before a client run.
- Ship only your mod and a list of the others with their official links. Never repack other people's jars.

## 4. World conversion (real world into Minecraft)
The RealWorldMC and Meld direction: map data, elevation or photogrammetry turned into a world.
- Keep the converter separate from the data. Check each data source's licence (OpenStreetMap is ODbL and
  needs attribution) and write it into the world's README.
- 1 block = 1 metre unless the user picks another scale; record it.
- Prior art: RealWorldMC (realworldmc.com), the pinned project on Mineplus.

## Building a 26.x Fabric mod
Minecraft 26.x ships without obfuscation: Loom's non-remapping plugin `net.fabricmc.fabric-loom`, no
`mappings` line, Mojang's class names, JDK 25. Use Fabric's example mod for the target version as the start.

## Done means
- It loads in a clean profile with only its declared dependencies.
- The guest's numbers in `MODLOG.md` match what the mod does (a test or a recorded measurement).
- No guest or Minecraft assets in the repo; credits for every source.
