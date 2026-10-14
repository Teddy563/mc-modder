---
description: Start a new Minecraft crossover project (Minecraft inside another game) from the MC Modder template
argument-hint: <host game> [project folder]
---

Host game: **$1**. Project folder: **$2** (if empty, use `../<host>-minecraft`, next to this toolkit's folder,
never inside it).

1. Load the `mc-modder` skill and follow it. Read the host's section in `host-adapters`. If the host isn't listed,
   say so and do the recon from that skill's last section.
2. Ask the user for anything you can't find: the host's exact build and store, which edition, the Minecraft version
   they want, and what they want from the crossover (real Minecraft running, or only its look or rules). If they only
   want the look or rules, switch to `mc-merge` and stop here.
3. Run `um mc scan`. If there is no JDK 25, say so now: the bridge can't be built until one is installed.
4. Create the project folder outside this repo and `git init` it. Copy `examples/minecraft-gta5-passthrough/mc/`
   and `examples/minecraft-gta5-passthrough/host/` into it. Copy `gta/` only when the host is GTA V.
5. Unless the host is GTA V, strip the GTA gameplay code exactly as `minecraft-bridge` says ("Starting a new host").
6. Rename for this project: `fabric.mod.json` `id`, the Java package, `FrameExporter.NAME` (the shared-memory name),
   the default port in `HostLink`, `rootProject.name`. Pick a port other than 25599 so it can run next to the GTA V
   bridge.
7. Build it (`./gradlew build`, or `.\gradlew.bat build` on Windows) and run its GameTests. Fix the build before
   going on; nothing GTA may remain (`grep -rn "MobWar\|Nether\|ProxyTargetGoal" mc/src` is empty).
8. Write `MODLOG.md`: host build, loaders and versions (see `docs/VERSIONS.md`), route and why, closest prior
   project, backup and restore commands (`um backup create`), the Minecraft profile you'll use (a dedicated one).
9. Write `docs/CONTRACT.md` from `knowledge/techniques/bridge-contracts-ownership-units-and-lifecycle.md`, filled in
   for this host: ownership, units, axis mapping, link messages, frame layout, failure behaviour.
10. Run `python <toolkit>/tools/mc_check.py <project>` and `python <toolkit>/tools/mc_check.py --stale <project>`;
    both must report 0 problems.
11. Propose the first slice (one value crossing, logged on both sides) and wait for the user's go-ahead before
    installing anything into the game folder.
