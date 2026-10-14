---
name: host-adapters
description: Per-host notes for putting Minecraft inside another game - GTA V, GTA IV, Skyrim, Fallout 4, Fallout New Vegas, Elden Ring, Cyberpunk 2077 - with the hook framework, units, axis mapping, anti-cheat line and the closest reviewed prior project for each. Use when starting or debugging the host-game half of a Minecraft passthrough mod.
---

# Host adapters

The host half is never generic: each bridge needs its own camera hook, safe game-thread entry, collision
query, depth buffer and input routing. Start from the closest prior project, read its README and design
doc, and copy its units and ownership decisions into `docs/CONTRACT.md`.

Versions below are the ones each project named (from the Mineplus list, checked 2026-10-14). Mineplus
pages: `https://mineplus.net/p/<id>/`. A project's README is its creator's report; none of these were
play-tested by Mineplus.

## GTA V
- **Template:** `examples/minecraft-gta5-passthrough/` (frame compositing + state). Tested by its author on GTA V Legacy
  build 3889, ScriptHookV 3889.0, ReShade 6.8.0, Minecraft 26.3.
- **Hooks:** ScriptHookV ASI for gameplay (camera, ground probes, natives); a ReShade add-on + `.fx` effect
  for compositing against GTA's reversed-Z depth. ReShade must load as `ReShade64.asi` through the ASI
  loader: GTA loads the system `dxgi.dll` ahead of a proxy.
- **Units:** 1 m = 1 block; (x, y, z) → (x, z + yOffset, −y); yaw = 180 − heading.
- **Line:** story mode only, `-nobattleye`. Enhanced (DX12) is not supported by the template.
- **Prior art:** `minecraft-gta-v` (this template), `wither-storm-gta-v` (Forge 1.20.1 content mod over the
  same bridge), `grandtheftminecraft` (Minecraft rebuilt inside GTA, not passthrough).

## GTA IV
- **Hooks:** an ASI plugin (Ultimate ASI Loader); D3D9.
- **Units:** 1 m = 1 block.
- **Prior art:** `libertycraft` (fork of SkyCraft, geometry transfer, Linux/Proton first, downgrades to
  1.0.8.0 with FusionFix + ZolikaPatch; its ASI plugin is GPL-3.0, so a derivative of that part must be too),
  `minecraft-passthrough-iv` (CE 1.2.0.59, Minecraft 26.3).

## Skyrim (SE/AE)
- **Hooks:** SKSE64 plugin + Address Library; D3D11. Draw inside Skyrim's world pass for native lighting.
- **Units:** ~70 Skyrim units per block.
- **Ownership:** Minecraft owns movement; Skyrim takes over for furniture, mounts and kill-moves (SkyCraft).
- **Gotchas from SkyCraft's README:** camera mods (Improved Camera SE, SmoothCam, TDM) conflict; the Helgen
  opening can leave you stuck, use Alternate Start.
- **Prior art:** `skycraft` (the project that started the trend, AE runtime 1.7.104, Minecraft 26.3, MIT).
  Its Fabric mod exports meshes and atlases instead of a picture: read it before choosing compositing.

## Fallout 4
- **Hooks:** F4SE 0.7.9+ plugin + Address Library; D3D11.
- **Units:** Bethesda scale, ~70 units per block (check against the project).
- **Prior art:** `falloutcraft` (1.11.240, SkyCraft lineage; Minecraft 26.3 Fabric or 1.21.1 NeoForge).

## Fallout: New Vegas
- **Hooks:** xNVSE plugin + ReShade (D3D9); runs well under Proton/DXVK.
- **Units:** 70 units per block, exterior yOffset −34 (NewVegasCraft).
- **Transport:** WebSocket + mapped file, like the GTA V template.
- **Prior art:** `new-vegascraft` (Steam 1.4.0.525, no other ReShade or `d3d9.dll` mods).

## Elden Ring
- **Hooks:** a native DLL loaded by `me3` (or ModEngine2); D3D12, so frame readback goes through buffers,
  not textures.
- **Line:** offline only, launched through me3 with EasyAntiCheat off, a separate save file. Never online.
- **Units:** 1 m = 1 block; damage is scaled by the target's max HP in the CrossOver bridge.
- **Prior art:** `eldencraft` (exe 2.7.1.0, Minecraft 26.3, checksum-verified launcher, separate
  `EldenCraft.sl2`), `minecraft-ring` (app 1.17.1, Minecraft 1.21.1, D3D12 bridge),
  `minecraft-crossover-bridge` (Apple Silicon via CrossOver, also Monster Hunter: World).

## Cyberpunk 2077
- **Hooks:** RED4ext (native plugins) and Cyber Engine Tweaks (Lua) for gameplay; D3D12 for the picture.
- **Line:** single-player only; no anti-cheat in single-player, but keep it offline anyway.
- **Units:** metres, Z-up: start from the GTA V mapping and verify with a marker.
- **Prior art:** none reviewed yet. Mineplus lists `minepunk-duocor3`, `cyberblock-rodthegod2` and
  `cybercraft-itzbloxy` as unreviewed: read them as leads, not as working references.

## A host that isn't here
1. Check the Mineplus list and `skills/mashup-mods/references/mashup-cases.md`.
2. Find the host's script extender or plugin loader, its graphics API, and its anti-cheat.
3. First slice: the host plugin logs one line, then sends the player's x to the bridge and both sides log it
   with a frame counter.
4. Add the host's section here when it works, with exact versions.
