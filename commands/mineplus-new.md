---
description: Start a new Minecraft crossover project from the Mineplus Modder template
argument-hint: <host game> [project folder]
---

Start a Mineplus Modder project for putting Minecraft into **$ARGUMENTS**.

1. Load the `mineplus-modder` skill and follow it. Read `host-adapters` for this host. If the host isn't
   listed, say so and do the recon from that skill's last section.
2. Ask the user for anything you can't find: the host's exact build and store, which edition, the
   Minecraft version they want, and what they want from the crossover (real Minecraft running, or only its
   look or rules). If they only want the look or rules, switch to `mc-merge` and stop here.
3. Create the project folder (the second argument, or `./<host>-minecraft`). Copy
   `examples/minecraft-gta5-passthrough/mc/` and `examples/minecraft-gta5-passthrough/host/` into it. Copy the GTA side
   (`gta/`) only when the host is GTA V.
4. Write `MODLOG.md`: host build, loader and versions, route and why, closest prior project, backup and
   restore commands.
5. Write `docs/CONTRACT.md` from the `minecraft-bridge` skill's contract section, filled in for this host:
   ownership, units, axis mapping, link messages, frame layout, failure behaviour.
6. Propose the first slice (one value crossing, logged on both sides) and wait for the user's go-ahead
   before installing anything into the game folder.
