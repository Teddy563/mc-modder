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
| **Real world into Minecraft** | map data or photogrammetry converted into a world (the RealWorldMC and Meld angle) | `mc-merge`, section "World conversion" |

Pick the lightest route that delivers the idea. Running two games at once for one mechanic is the most
common mistake: if the user only wants the guest's look or one rule, port it instead.

## 2. Find prior art before writing code
1. Search the Mineplus list: https://mineplus.net/projects/?q=<host game>. Every project there has a page at
   `/p/<id>/` with its requirements, versions and repo. Read the closest project's README and design doc.
2. Check the host's reference in `host-adapters/references/`. It names the hook framework, units, axis
   mapping and the reviewed prior projects.
3. Treat any README as the creator's report until you've run it. Many listed projects are marked
   `unreviewed` on Mineplus; nobody has play-tested them.

## 3. The loop
1. **Recon.** Exact host build, store (Steam/GOG/Epic), edition (GTA V Legacy vs Enhanced, Skyrim SE vs AE),
   loader availability for that build, anti-cheat. Write it into `MODLOG.md`.
2. **Back up.** Saves, the game folder's loader files, the Minecraft profile. Write the one-line restore
   command into `MODLOG.md`.
3. **Contract.** Before any code, write `docs/CONTRACT.md`: who owns the player and when control moves,
   units (1 block = ? host units), axis mapping, the link messages, frame layout, what happens when one
   side dies. `minecraft-bridge` has the default contract.
4. **First slice.** One float crosses and is logged on both sides with a frame counter. Then the camera.
   Then the ground. Then the picture. Only then gameplay.
5. **Test without the host.** The GTA V template has `host/fakehost.py` and `gta/tests/fakegta.cpp`; build
   the same stand-in for a new host before touching the real game.
6. **Verify in the real game,** offline, with the user at the keyboard for anything that touches menus.
7. **Package.** Code and converters only; never game files, Minecraft jars or extracted assets.
8. **Write it up** (`MODLOG.md`, and a field note in `knowledge/` with `um kb new`, and a PR upstream if the user agrees).
9. **Submit to Mineplus** at https://mineplus.net/submit/ (or contact@mineplus.net), with repo, video and
   exact versions. Publishing anything is the user's call.

## 4. Templates
- `examples/minecraft-gta5-passthrough/`: Minecraft 26.3 Fabric ⇄ GTA V Legacy (ScriptHookV + ReShade add-on).
  Frame compositing + state over a 127.0.0.1 WebSocket and named shared memory. Universal Modder's worked example; its field note is
  `knowledge/games/gta-v/minecraft-passthrough.md`. Start any new host from its `mc/` folder: the Fabric half is host-agnostic apart from the GTA-specific gameplay classes (`MobWar`, `Nether`, parts of
  `WorldBridge`).
- `/mc-new <host>` copies the template into a new project folder and writes the first `MODLOG.md`
  and `docs/CONTRACT.md` for that host.

## 5. Safety
Read `references/safety.md` before the first modded launch. The short version: offline single-player only,
never near anti-cheat, never publish game files, never link the known malware lures, never re-host other
people's builds or videos, credit every creator you build on.
