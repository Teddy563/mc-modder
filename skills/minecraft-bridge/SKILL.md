---
name: minecraft-bridge
description: The Minecraft (Fabric) half of a passthrough mod - the 127.0.0.1 link the host game talks to, the colour/depth/overlay frame export through shared memory, camera and ground sync, and the coordinate contract. Use when building or changing the Minecraft side of "Minecraft inside another game", or when writing a new host plugin that has to speak to it.
---

# The Minecraft bridge

Every passthrough has the same Minecraft half. Start from `examples/minecraft-gta5-passthrough/mc/` (Fabric,
Minecraft 26.3, JDK 25) instead of writing a new one. It is not host-neutral yet: the GTA V gameplay code is
compiled in, and `HostLink` imports it, so follow "Starting a new host" below before building for another game.

## What the Fabric mod does
| Class (`dev.rehan.passthrough`) | Job | Keep for a new host? |
|---|---|---|
| `client/HostLink` | WebSocket server on `127.0.0.1:25599` (`-Dpassthrough.port`) | yes, minus the GTA cases |
| `client/HostState`, `client/PlayerSync`, `client/mixin/CameraMixin` | render from the host's camera; Steve stands on the host player's feet | yes |
| `client/FrameExporter`, `client/SharedMemory` | world colour + depth and a hand/HUD overlay into `Local\MCPassthroughFrame` | yes (rename the mapping) |
| `client/ClientInput` | mouse buttons, wheel, hotbar forwarded from the host (the host keeps focus) | yes |
| `client/mixin/FogRendererMixin` and the other client mixins | no sky, fog, clouds, bobbing; keeps rendering unfocused | yes |
| `WorldBridge` | ground columns → barrier blocks, block sync, explosions, projectiles | yes, minus the `MobWar`/``grep -rn "MobWar|Nether|ProxyTargetGoal" src` returns nothing.` calls |
| `MobWar`, ``grep -rn "MobWar|Nether|ProxyTargetGoal" src` returns nothing.`, `ProxyTargetGoal`, mixins `MobMixin`, `MobAccessor`, `PortalMixin`, `ProjectileMixin`, `ProxyMixin` | GTA's mobs-vs-police, the Nether takeover, projectiles traced through GTA | no |

## Starting a new host
`/mc-new <host>` does this; by hand:
1. Copy `mc/` and `host/` into a new folder outside this repo and `git init` it.
2. Delete `MobWar.java`, ``grep -rn "MobWar|Nether|ProxyTargetGoal" src` returns nothing..java`, `ProxyTargetGoal.java` and the mixins `MobMixin`, `MobAccessor`,
   `PortalMixin`, `ProjectileMixin`, `ProxyMixin`, and remove them from `passthrough.mixins.json`.
3. In `HostLink.onMessage` remove the cases `projhit`, `peds`, `mobdmg`, `spawnmobs`, `mobsclear`, `portal`,
   `netheroff`, `nethersync`, `glide`, and rename the relay types `gta`, `gtastate`, `gtainfo` to your host's.
   In `WorldBridge` remove the `MobWar.tick`, ``grep -rn "MobWar|Nether|ProxyTargetGoal" src` returns nothing..tick`, `Nether.onBlockChanged` and `Nether.isGround`
   calls; in `Passthrough` the two `detach` calls.
4. Rename together: `fabric.mod.json` `id`, the Java package, `FrameExporter.NAME`, the default port in
   `HostLink`, `rootProject.name`. Two bridges on one PC must never share the mapping name or the port.
5. Build (below). It must compile with nothing GTA left: `grep -rn "MobWar\|Nether\|ProxyTargetGoal" src`
   returns nothing.

## Link protocol (JSON text frames, Minecraft coordinates)
Host → Minecraft:
- `{"t":"cam","f":frame,"p":[x,y,z],"r":[yaw,pitch,roll],"fov":vfov_deg,"fp":bool,"pl":[x,y,z],"h":body_yaw}` every host frame
- `{"t":"ground","c":[x,z,yBottom,yTop, ...]}` solid columns around the player (become barriers); `{"t":"clear"}`
- `{"t":"cmd","c":"time set noon"}` a server command
- `{"t":"key","k":"use|attack|pick|inventory|drop|swap|escape","down":bool}`, `{"t":"slot","n":0-8}`,
  `{"t":"scroll","d":±1}`, `{"t":"hud","hidden":bool}`, `{"t":"view","w":px,"h":px}`

Minecraft → host: `{"t":"hello","v":1,"shm":"Local\\MCPassthroughFrame","pid":…}` on connect,
`{"t":"explosion","pos":[x,y,z],"r":radius}`, and gameplay events (`proj`, `mobs`, `mobhit`, `hot`).
Messages typed `gta`, `gtastate`, `director` are relayed to the other clients unchanged; a new host can reuse
that relay under its own names.

## Frame layout
Named mapping `Local\MCPassthroughFrame`, little-endian, header 4096 bytes, three slots. The full byte map
is the comment at the top of `FrameExporter.java`; `host/mcframe.py` reads it in Python. Per slot: a
seqlock (`seq` odd while writing), the pose the frame was rendered with, near/far/fov, depth flags, then
three `width × height × 4` layers (world RGBA premultiplied, world depth float32, overlay RGBA). Always
composite with the pose stored in the slot, not the latest camera you sent.

## Coordinate contract
Write it into `docs/CONTRACT.md` for each host. Defaults that worked:
- 1 host metre = 1 block when the host uses metres (GTA V, GTA IV, Elden Ring). Bethesda hosts use
  ~70 units per block (SkyCraft, NewVegasCraft).
- Z-up host (x, y, z) → Minecraft (x, z + yOffset, −y). Pick `yOffset` so the ground under the player lands
  on a whole block, and re-level when nothing is built nearby.
- Minecraft yaw = 180 − host heading, pitch = −host pitch (GTA V). Check signs with one marker before
  trusting them.
- Who owns the player: the host on foot, Minecraft while flying (GTA V template). Write down how control
  comes back.

## Build and run
1. **JDK first.** Minecraft 26.x needs a JDK 25 to build. Launcher-bundled runtimes (`.minecraft/runtime`,
   Modrinth's `meta/java_versions`) are JREs and can't compile. `um mc scan` lists every Java on the machine and
   says which are JDKs. If `java -version` on PATH isn't 25, set `org.gradle.java.home=<JDK 25 path>` in
   `~/.gradle/gradle.properties` (not the project's, it's machine-specific).
2. **No mappings.** 26.x ships unobfuscated: Loom's non-remapping plugin `net.fabricmc.fabric-loom`, no `mappings`
   line, `implementation` (not `modImplementation`), `jar` (not `remapJar`), Mojang class names (`Minecraft`, not
   `MinecraftClient`). `tools/mc_check.py --stale <folder>` flags the old forms.
3. **Build:** `cd mc && ./gradlew build` (Windows: `.\gradlew.bat build`) → `build/libs/<name>-<version>.jar`.
4. **Dev client:** `./gradlew runClient` starts Minecraft with the mod from source, offline account, game dir
   `mc/run`. Logs: `run/logs/latest.log`, crashes in `run/crash-reports/`, JVM crashes as `hs_err_pid*.log`.
5. **A real profile:** give the bridge its own launcher profile and game directory (it changes options and opens a
   void world called `passthrough` by itself). Never install it into a play profile with other mods. Copy the jar
   and Fabric API into that profile's `mods/`; `um mc scan` lists the profiles and how many mods each has.

## Verify
- **GameTests** (`mc/src/gametest/`, Fabric's test API): `./gradlew build` runs the server GameTests (report in
  `build/run/gameTest/junit.xml`); `./gradlew runClientGameTest` starts a real client that connects to `HostLink`,
  checks the hello, sends `cam` and `ground`/`clear`, takes screenshots (`build/run/clientGameTest/screenshots/`)
  and, on Windows, checks the shared-memory header. Add a test for every message you add. CI runs both in
  `.github/workflows/mc-template.yml`.
- **Fake host:** `python host/fakehost.py 10` (Windows Python with `websockets`, `numpy`, `Pillow`) flies the
  camera round test blocks over a flat ground and composites the frames over a synthetic scene; the PNGs show
  whether alignment and occlusion are right. `host/place_test.py` and `host/tnt_test.py` check block sync and
  explosion events.
- **Real host:** only after both pass. Record it (`showcase-video`) and write down what was verified and what
  wasn't (`knowledge/techniques/evidence-levels-for-mashup-claims.md`).
- More: `knowledge/techniques/a-scenario-harness-in-a-minecraft-fabric-dev-client-real-cli.md`,
  `knowledge/techniques/oracles-how-agents-know-a-mod-works.md`.

## Mixins
Passthrough mods stack many renderer mixins, often next to Sodium or Iris.
- Look before you write: the `minecraft-dev` MCP server (in this repo's MCP config) serves decompiled source and
  checks a mixin's target and an access widener against the real game. Run its mixin check on every new mixin, and
  its version diff before moving a mixin to another Minecraft version.
- Prefer MixinExtras `@WrapOperation` and `@ModifyExpressionValue` (they chain with other mods) over `@Redirect`
  and `@Overwrite` (they don't). Prefix every `@Unique` field and method with the mod id.
- The template's dev run has `-Dmixin.debug.export=true -Dmixin.dumpTargetOnFailure=true`: patched classes land in
  `run/.mixin.out/`, and a failed injection dumps its target.

## Older Minecraft versions
Some hosts' prior projects use Minecraft 1.21.1 (Fabric or NeoForge) or 1.20.1 Forge (Wither Storm × GTA V,
to run an existing content mod). The protocol and frame layout carry over; the mixins don't. Port the mixins
by reading the target version's renderer, not by guessing names.
