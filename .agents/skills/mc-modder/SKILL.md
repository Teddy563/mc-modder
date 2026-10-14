---
name: mc-modder
description: Build Minecraft crossover mods with an AI agent - real Minecraft running inside another PC game (passthrough), another game's content or rules inside Minecraft, or Minecraft merged with another mod or concept. Use when the user wants Minecraft in Skyrim, GTA V, Elden Ring, Cyberpunk 2077, Fallout or any other host, wants a game ported into Minecraft, or wants to combine Minecraft with another mod. Start here; it routes to minecraft-bridge, host-adapters and mc-merge.
---

# MC Modder

MC Modder is a fork of
[Universal Modder](https://github.com/rehan-remade/universal-modder) (MIT, by Rehan and contributors).
This fork keeps every Universal Modder skill and adds a Minecraft-first layer on top. For work that leaves
Minecraft (another engine, fal assets, video), use `mod-any-game`, `fal-assets` and `showcase-video` from this
repo.

## 1. Pick the direction
Ask the user if it isn't clear. Each direction has its own skill.

| Direction | What it means | Go to |
|---|---|---|
| **Minecraft into a host** | real Minecraft Java runs next to the host game; the host draws it, sends camera and collision back | `minecraft-bridge` + `host-adapters` |
| **A game into Minecraft** | the guest's content, mechanics or rules rebuilt as a Fabric mod; the guest never runs | `mc-merge` |
| **Merge with a mod or concept** | Minecraft plus another Fabric/Forge mod, a modpack, or an idea (a boss, a vehicle, a game mode) | `mc-merge` |
| **Real world into Minecraft** | map data or photogrammetry converted into a world (the RealWorldMC and Arnis angle) | `mc-merge`, section "World conversion" |

Pick the lightest route that delivers the idea. Running two games at once for one mechanic is the most
common mistake: if the user only wants the guest's look or one rule, port it instead.

## 2. Read first
Every Minecraft task:
- `skills/mod-any-game/references/engines/minecraft.md`: loaders, versions, where things live.
- `knowledge/techniques/fabric-mod-for-26-x-without-mappings.md`: how a 26.x Fabric mod is built.
- Testing: `knowledge/techniques/a-scenario-harness-in-a-minecraft-fabric-dev-client-real-cli.md`,
  `fabric-1-20-1-gametests-as-the-oracle-of-a-large-mod-port.md`,
  `neoforge-1-21-1-gametests-for-mob-ai-real-survival-players-s.md`,
  `testing-a-fabric-mod-inside-a-large-modpack-headless.md` (all in `knowledge/techniques/`).

Minecraft into a host, also:
- `knowledge/techniques/`: `choosing-a-mashup-route.md`, `bridge-contracts-ownership-units-and-lifecycle.md`,
  `frame-compositing-depth-and-pose-sync.md`, `geometry-transfer-host-draws-guest-meshes.md`,
  `collision-and-combat-bridging.md`, `evidence-levels-for-mashup-claims.md`, and `d3d12-frame-readback-buffers-only.md`
  for D3D12 hosts.
- Field notes from bridges built on the GTA V template: `knowledge/games/gta-v/minecraft-passthrough.md`,
  `knowledge/games/beamng-drive/`, `knowledge/games/portal-2/portalcraft-minecraft-inside-portal-2.md`,
  `knowledge/games/gothic-ii/`, `knowledge/games/mount-and-blade-ii-bannerlord/bannercraft-minecraft-gameplay-bridge.md`.

## 3. Find prior art before writing code
1. `um kb search "<host game>"` and `um kb search minecraft` for field notes in this repo.
2. The host's section in `skills/host-adapters/SKILL.md`: hook framework, units, axis mapping, prior projects.
3. The Mineplus list (https://mineplus.net/projects/?q=<host game>, one page per project at `/p/<id>/`; skip it if
   the site doesn't load) and
   `skills/mashup-mods/references/mashup-cases.md`. Read the closest project's README and design doc.
4. Treat any README as the creator's report until you've run it. Many listed projects are marked `unreviewed`;
   nobody has play-tested them.

## 4. The loop
1. **Recon.** `um mc scan` (Java runtimes and which are JDKs, launchers, profiles with game and loader versions)
   and the `game-recon` skill for the host: exact build, store, edition (GTA V Legacy vs Enhanced, Skyrim SE vs AE),
   loader availability, anti-cheat. Write it into `MODLOG.md`.
2. **Back up.** `um backup create` for the host's saves and config and for the Minecraft profile you'll use
   (`.minecraft`, a Modrinth `profiles/<name>`, or a Prism `instances/<name>`). Write the restore command into
   `MODLOG.md`. Use a dedicated Minecraft profile, never a play profile.
3. **Contract.** Before any code, write `docs/CONTRACT.md` from
   `knowledge/techniques/bridge-contracts-ownership-units-and-lifecycle.md`: who owns the player and when control
   moves, units, axes, link messages, frame layout, what happens when one side dies.
4. **First slice.** One value crosses and is logged on both sides with a frame counter. Then the camera, the
   ground, the picture. Only then gameplay.
5. **Test without the host.** GameTests and the fake host (`minecraft-bridge`, "Verify"); for a new host, a
   stand-in like the template's `gta/tests/fakegta.cpp` before touching the real game.
6. **Verify in the real game,** offline, with the user at the keyboard for anything that touches menus. Stop
   processes by PID (`um win kill <pid>`), screenshots with `um win shot`.
7. **Package.** `python tools/mc_check.py <project>` and `um publish check --game <host install>`; then the
   `publish-mod` skill. Code and converters only; never game files, Minecraft jars or extracted assets.
8. **Write it up.** `MODLOG.md`, then a field note: `um kb new`, `um kb check`, and `um kb pr` once the user
   agrees (`share-field-notes`). Video: `showcase-video`.
9. **Submit to Mineplus** at https://mineplus.net/submit/ (or contact@mineplus.net) with repo, video and exact
   versions. Publishing anything is the user's call.

## 5. Templates and starting points
- **Minecraft into a host:** `examples/minecraft-gta5-passthrough/` (Minecraft 26.3 Fabric ⇄ GTA V Legacy,
  ScriptHookV + ReShade add-on, frame compositing + state over a 127.0.0.1 WebSocket and named shared memory).
  Its Fabric half is the starting point for every host, but the GTA gameplay code is compiled in: follow
  `minecraft-bridge`, "Starting a new host". `/mc-new <host>` does it for you.
- **Content mods, ports and merges:** don't copy the GTA template. Start from `FabricMC/fabric-example-mod` at the target
  version's branch, or the web generator at https://fabricmc.net/develop/template/; see `mc-merge`.
- Generic Minecraft modding knowledge (datagen, resource packs, CI and release) is covered well by
  [Jahrome907/minecraft-agent-skills](https://github.com/Jahrome907/minecraft-agent-skills) (MIT). Use it next to
  this toolkit rather than reinventing it here.

## 6. Safety
Read `references/safety.md` before the first modded launch. The short version: offline single-player only,
never near anti-cheat, never publish game files, never link the known malware lures, never re-host other
people's builds or videos, credit every creator you build on.
