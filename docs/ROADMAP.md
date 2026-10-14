# MC Modder roadmap

From three research passes on 2026-10-15: an audit of this fork's Minecraft layer, a survey of Minecraft
modding tools for AI agents ([research/research-tools.md](research/research-tools.md)), and a read of twelve
passthrough projects ([research/research-passthrough.md](research/research-passthrough.md)). Nothing listed
here was play-tested. Effort: S = under an hour, M = a few hours, L = days.

## The short version
The skills explain the ideas well. Two things are weak:
1. **Agents can't verify their work.** There are no run or test steps, the template has no GameTests, and
   nothing tests the shipped jar.
2. **There's no reusable code.** Every new host copies the whole GTA V project, GTA gameplay code included.
   NewVegasCraft and Wither Storm × GTA V both did, kept the same port and mapping name, and can't run side by side.
   SkyCraft's family went the other way: Killcraft runs SkyCraft's jar unchanged plus an add-on.

## Tier 1: fix what's wrong (all S, do first)
- [ ] **Stop calling the template host-agnostic.** `HostLink.java` imports `MobWar` and `Nether`; deleting them
  breaks the build. Give the exact strip list (MobWar, Nether, ProxyMixin, ProjectileMixin, ProxyTargetGoal,
  the GTA relay in HostLink) in `minecraft-bridge` and `mc-modder` §4.
- [ ] **Fix broken references:** `host-adapters/references/` doesn't exist; the "World at War" note cited in
  `mc-merge` isn't in `knowledge/`; `mc_check.py`'s docstring names old paths;
  `engines/minecraft.md` points to a `minecraft-modding-mcp` that doesn't exist.
- [ ] **Run and verify steps** in `minecraft-bridge` and `mc-merge`: `./gradlew runClient`, or build and copy the
  jar into a dedicated profile's `mods/`; where `latest.log` and `crash-reports/` are; GameTests and client game
  tests, with links to the four Fabric/NeoForge test notes in `knowledge/techniques/`.
- [ ] **JDK check before any build.** 26.x needs a JDK 25; launcher-bundled runtimes are JREs and can't compile.
  Set `org.gradle.java.home` or a Gradle toolchain.
- [ ] **Fix `/mc-new`:** use `$1`/`$2`, create the project outside the toolkit and `git init` it, rename mod id,
  package, port and shared-memory name, apply the strip list, run `tools/mc_check.py` and `um publish check`,
  base `CONTRACT.md` on `knowledge/techniques/bridge-contracts-ownership-units-and-lifecycle.md`. Add
  `.claude/commands/mc-new.md` so it also loads in a clone.
- [ ] **A "read first" list in `mc-modder`:** `engines/minecraft.md`, `fabric-mod-for-26-x-without-mappings`, the
  GameTest/harness/modpack notes, the passthrough technique notes, the BeamNG and Portal 2 notes (both built on
  this template). Route recon, packaging and video to `game-recon`, `publish-mod`, `showcase-video`.
- [ ] **Name the `um` tools in the loop:** `um backup create` with the `.minecraft`, Modrinth and Prism profile
  paths, `um publish check`, `um kb search/check/pr`.
- [ ] **`tests/test_mc_check.py`:** self-test cases, the repo is clean, and every path the four skills and the
  command mention exists. This puts the layer under CI.
- [ ] **Harden `mc_check`:** more text types (.ts .lua .ps1 .cmd), `raw.githubusercontent` and `codeload` URL forms,
  more binary types (.class .pak .esp .esm .esl .mca .pdb), the wrapper jar only under `gradle/wrapper/`.

## Tier 2: make agents much better at Minecraft (S–M)
- [ ] **minecraft-dev-mcp** ([MCDxAI/minecraft-dev-mcp](https://github.com/MCDxAI/minecraft-dev-mcp), MIT, 26.1+):
  add it to `mcp.json`; decompiled source, mixin and access-widener checks, version diffs. Tell `minecraft-bridge`
  and `port-a-mod` to check every mixin target with it. S
- [ ] **GameTests + a client game test in the template's `mc/`** (Fabric's `configureTests`, `src/gametest`). The
  client test opens the void world, sends a fake `cam`, takes a screenshot and checks the shared-memory header,
  turning `fakehost.py`'s PNG into pass/fail. Require one GameTest per mechanic in `mc-merge`'s "Done means". M
- [ ] **Pre-26 snippet check** in `um publish check` (or a hook): old `fabric-loom` id, a `mappings` line,
  `modImplementation`, `remapJar`, Java 21, Yarn names like `MinecraftClient`. The most common model mistake on 26.x. S
- [ ] **CI that boots the shipped jar:** [headlesshq/mc-runtime-test](https://github.com/headlesshq/mc-runtime-test)
  (MIT, 26.1–26.3) runs `/test runall` in a headless client and fails when no test ran. S
- [ ] **Mixin rules** in `minecraft-bridge`: MixinExtras `@WrapOperation`/`@ModifyExpressionValue` over
  `@Redirect`/`@Overwrite`, `@Unique` with a modid prefix, `-Dmixin.debug.export=true` in the dev run. S
- [ ] **Reuse [Jahrome907/minecraft-agent-skills](https://github.com/Jahrome907/minecraft-agent-skills)** (MIT,
  checked on 26.3) for generic testing, CI/release, resource packs and datagen instead of rewriting them; credit
  it. Start non-passthrough mods with Fabric's `fabric init` instead of the GTA template. M
- [ ] **Version matrix** (Minecraft → Java → loader → Fabric API → Loom → Gradle), refreshed from Fabric Meta;
  recheck the template's Fabric API pin. M
- [ ] **Minecraft recon** (`um mc scan`): launchers, profiles with game and loader versions, JREs vs JDKs, Loom
  cache. M
- [ ] **Agent play-testing** with [denfry/mcpfabric](https://github.com/denfry/mcpfabric) in a dev-only profile
  (screenshots, commands, pathfinding). Operator-level by default: never ship it in a release. M
- [ ] **host-adapters:** sections for BeamNG, Portal 2, Gothic II, Bannerlord; link the Elden Ring, Cyberpunk and
  Fallout 4 host notes and the D3D12 readback note. M

## Tier 3: a real bridge kit (M–L)
- [ ] **Split the guest mod into a host-agnostic core jar and per-host add-on jars.** Core: link, frame export,
  camera, input, collision. Add-on: gameplay. Mod id, mapping name, port and units from config. Proven by Killcraft
  on SkyCraft. L
- [ ] **A versioned binary protocol** (`PROTOCOL.md` + one header): magic and version, PIDs, heartbeats, epoch per
  channel, seqlocked state, event rings, freshness windows. Keep JSON over WebSocket for director commands only, with
  a token. Generate bindings with Orinkle's `ptgen` (MIT). Models: SkyCraft's header, EldenCraft's `PROTOCOL.md`. L
- [ ] **Minecraft-owns-movement mode** with a real collision field (host triangles fed to `Entity.collide`, as
  SkyCraft does) instead of barrier blocks; keep host-owns as the other mode. L
- [ ] **Fake guest + fake host per protocol**, with timeout, epoch and steep-wall scenarios and negative controls
  (Orinkle). M
- [ ] **Launcher/installer template:** portable Prism downloaded with a pinned SHA-256 at install time (never
  committed, GPL-3.0), idempotent install with a backup manifest and dry run, executable version check, separate host
  save (LibertyCraft, EldenCraft). M
- [ ] **Host-plugin skeleton:** fixed loader + swappable core DLL, every game address checked against expected
  bytes, game calls only on the game thread, refuses to start with anti-cheat present. M
- [ ] **Geometry-transfer exporter** (meshes, atlas, lights) as a hybrid with frames (EldenCraft). L
- [ ] **One source, several Minecraft versions** (26.3 Fabric, 1.21.1 NeoForge, 1.20.1 Forge) with FalloutCraft's
  preprocessor (MIT), so players can bring modpacks. L

## Licences for reuse
Copyable into MIT with their notices: SkyCraft, FalloutCraft, NewVegasCraft, EldenCraft, Minecraft-Ring,
minecraft-crossover-bridge (MinHook stays BSD-2), Killcraft, Orinkle's toolkit, LibertyCraft outside `asi/`.
Not copyable: LibertyCraft's `asi/` (GPL-3.0), ValCraft (no licence), Prism binaries.
