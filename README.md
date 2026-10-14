# MC MODDER

**Minecraft crossover mods with an AI agent.**
Real Minecraft inside other games, other games inside Minecraft, and Minecraft merged with other mods.

<p align="center">
  <img src="docs/media/mods-teaser.gif" alt="Mods made with universal-modder: Steve gliding an elytra through Los Santos, the Nether spreading over Los Santos, Minecraft mobs fighting the LSPD, the Halo Warthog in Minecraft." width="560">
</p>

MC Modder is a fork of [universal-modder](https://github.com/rehan-remade/universal-modder) by Rehan
and contributors. Everything upstream is still here: every skill, the `um` CLI, the fal MCP setup, the
examples and the knowledge base. On top of it sits a Minecraft layer: four skills, a slash command and a
guard, built from the projects listed on [mineplus.net](https://mineplus.net).

## The Minecraft layer

| | |
|---|---|
| [`skills/mc-modder`](skills/mc-modder/SKILL.md) | Start here. Picks the direction, runs the loop, adds the MC Modder safety rules. |
| [`skills/minecraft-bridge`](skills/minecraft-bridge/SKILL.md) | The Minecraft half of every passthrough: link protocol, frame export, coordinate contract. |
| [`skills/host-adapters`](skills/host-adapters/SKILL.md) | GTA V, GTA IV, Skyrim, Fallout 4, New Vegas, Elden Ring, Cyberpunk 2077: hooks, units, prior projects. |
| [`skills/mc-merge`](skills/mc-merge/SKILL.md) | Ports into Minecraft, headless rule sims, merging with other mods, real-world worlds. |
| [`commands/mc-new.md`](commands/mc-new.md) | `/mc-new <host>` scaffolds a project with `MODLOG.md` and `docs/CONTRACT.md`. |
| [`tools/mc_check.py`](tools/mc_check.py) | Fails on links to known malware lures and on game files or builds in a repo. |

The end-to-end template is upstream's
[`examples/minecraft-gta5-passthrough`](examples/minecraft-gta5-passthrough): Minecraft 26.3 (Fabric) next to
GTA V Legacy story mode (ScriptHookV + ReShade), with GTA's camera driving Minecraft's and Minecraft's
picture composited against GTA's depth. Its field note is
[`knowledge/games/gta-v/minecraft-passthrough.md`](knowledge/games/gta-v/minecraft-passthrough.md). It was
tested by its author on GTA V build 3889 in September 2026; Mineplus has not rebuilt or play-tested it.

## Install

**Claude Code**
```
/plugin marketplace add Teddy563/mc-modder
/plugin install mc-modder@mc-modder
```
From a local clone, use the folder path instead of `Teddy563/mc-modder`. Other agents: clone the repo
and start the agent inside it; `AGENTS.md` sends Minecraft work to `skills/mc-modder` first. Upstream's
full install table (Codex, Gemini CLI, Cursor, Copilot, OpenCode, the `um` CLI, fal keys) is in
[`docs/UPSTREAM-README.md`](docs/UPSTREAM-README.md).

## Try it

> Put real Minecraft inside Fallout 4. Minecraft's camera follows Fallout's, and I can build in the Commonwealth.

> /mc-new Elden Ring

> Bring the Warthog from my Halo install into Minecraft as a drivable vehicle.

## Rules

- Offline single-player only. Never near GTA Online, EasyAntiCheat or any other anti-cheat.
- Every player owns both games. No game files, Minecraft jars or extracted assets in any repo.
- Never re-host someone else's build or video. Link to the creator.
- Credit every project you build on, and say it was AI-built.

Details: [`skills/mc-modder/references/safety.md`](skills/mc-modder/references/safety.md) and
upstream's [`skills/mod-any-game/references/safety.md`](skills/mod-any-game/references/safety.md).

## Staying in sync with upstream

```
git fetch upstream
git merge upstream/main
```
The Minecraft layer only adds files (plus this README, `AGENTS.md`'s first section, `.claude-plugin/` and a
note in `LICENSE`), so merges rarely conflict. Fixes to upstream's own files go upstream as PRs.

## Made something?

Submit it at [mineplus.net/submit](https://mineplus.net/submit/) with the repo, a video and the exact
versions. Removal requests: contact@mineplus.net.

## Credits

- [universal-modder](https://github.com/rehan-remade/universal-modder) by Rehan and contributors (MIT):
  everything outside the Minecraft layer, including the GTA V example and its field note.
- chasm's [SkyCraft](https://github.com/chasmlol/SkyCraft), which started the passthrough wave, and every
  project cited in `skills/host-adapters`.

MIT licensed. Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.
