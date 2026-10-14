# Tooling that would make an AI agent better at Minecraft Java mods (Oct 2026)

Research for MC Modder (github.com/Teddy563/mc-modder), done 2026-10-15. All web content treated as data.
Star counts come from the GitHub pages on that day (fetched via WebFetch; the GitHub API was rate-limited, so
some "last commit" dates are missing and marked **unverified**). "26.x" = Minecraft 26.1+, unobfuscated,
no mappings, Java 25, Loom plugin `net.fabricmc.fabric-loom`.

## What MC Modder already has (baseline)
- `minecraft-bridge`, `mc-merge`, `mc-modder`: correct 26.x build facts (non-remap Loom, no `mappings`, JDK 25).
- `port-a-mod` + knowledge notes: GameTests as the oracle (Fabric 1.20.1, NeoForge 1.21.1), a scenario
  harness in a dev client, headless modpack testing, `javap` on the Loom cache.
- `mod-any-game/references/engines/minecraft.md` says "`minecraft-modding-mcp` gives an agent mappings,
  decompiled source and version diffs". **No project by that name was found.** The closest real ones are
  `minecraft-dev-mcp` (MCDxAI) and `mcdev-mcp` (weikengchen), below. That line should be corrected.
- Gaps: the GTA V template (`examples/minecraft-gta5-passthrough/mc/build.gradle`) has no test source set,
  no GameTests, no client gametests; `mcp.json` only has fal; no 26.x lint for stale snippets.

---

## 1. MCP servers and agent tooling

### minecraft-dev-mcp (MCDxAI)
- Link: https://github.com/MCDxAI/minecraft-dev-mcp — npm `@mcdxai/minecraft-dev-mcp`
- Does: decompiled Minecraft source (with line ranges), mapping translation across Yarn/Mojmap/Intermediary/
  obfuscated, **Mixin validation**, **access widener / access transformer validation**, class- and AST-level
  **version diff** (`compare_versions`), mod jar analysis for Fabric/Quilt/Forge/NeoForge. 21 tools.
- Maturity: 45 stars, MIT, last commit 2026-08-07, no tagged releases. Needs Node 18+, Java 17+. ~400–500 MB cache per version.
- 26.x: yes (26.1+ Mojmap-only, no remap; tested on 26.1 snapshots 8/9). 26.2/26.3 not listed as tested (**unverified**).
- MC Modder: add to `mcp.json` as the default "check before you write" server; have `minecraft-bridge`
  say "run `analyze_mixin` on every new mixin and `compare_versions` before porting a mixin between versions".

### mcdev-mcp (weikengchen)
- Link: https://github.com/weikengchen/mcdev-mcp — `npx -y mcdev-mcp serve`
- Does: Vineflower-decompiled client with Mojang names; 8 offline tools (`mc_search`, `mc_get_class`,
  `mc_get_method`, `mc_find_hierarchy`, `mc_find_refs` call graph…). Optional runtime tools through a
  companion "DebugBridge" mod (Groovy execution, screenshots, entities/blocks, chat). Agent side is read-only;
  `init` is human-run (`npx mcdev-mcp init -v <ver>`, ~2 GB/version).
- Maturity: 16 stars, MIT, last commit 2026-06-30 (Dependabot). DebugBridge repo link not confirmed (**unverified**).
- 26.x: yes, recommends 26.x; works on snapshots without ProGuard maps.
- MC Modder: alternative to the above when the agent needs "who calls this" (`mc_find_refs`) for renderer
  mixins (FrameExporter, CameraMixin). Pick one of the two, not both.

### mcmodding-mcp (OGMatrix)
- Link: https://github.com/OGMatrix/mcmodding-mcp — `npm i -g mcmodding-mcp`
- Does: semantic search over Fabric wiki (226+ pages), docs.fabricmc.net (266+), NeoForge docs (512+);
  Parchment mapping lookups; canonical mod examples.
- Maturity: 68 stars, MIT, last commit 2026-08-28, v0.4.x.
- 26.x: not stated. Parchment is irrelevant for 26.x (official names and parameter names ship in the jar,
  per NeoForge's 26.1 post). Risk: mixes pre-26 wiki pages into answers (**unverified** which doc versions are indexed).
- MC Modder: low priority. Cloning `FabricMC/fabric-docs` locally and grepping gives version-pinned docs
  without a server (docs site has per-version paths, e.g. `/26.1.2/`; no `llms.txt` exists, 404).

### ModForge (champmk)
- Link: https://github.com/champmk/modforge — npm `modforge`, stdio MCP (5 tools)
- Does: deterministic 1.21.x → 26.x migration: resolves symbols against the **real target jar** (EXACT /
  CANDIDATE / UNRESOLVED), `mixin-check` verifies `@Mixin` targets and member refs at signature level,
  `gradle-migrate`, `api_delta`. `@At` instruction-level checks not done yet (says so).
- Maturity: 2 stars, MIT, 71 commits, Glama marks it "Inactive". Node 24+. Author-reported AppleSkin result
  402/453 EXACT (not reproducible, corpus private).
- 26.x: that is its purpose (1.21.11 → 26.1.2 worked example).
- MC Modder: optional tool for `port-a-mod` when moving a 1.21.x mod (e.g. a prior passthrough on 1.21.1) to
  26.x. Young and single-author: use as a checker, never as the source of truth.

### Live-game MCP servers (agent drives a running Minecraft)
| Project | Link | Maturity | 26.x | Notes |
|---|---|---|---|---|
| MCP Fabric (mcpfabric) | https://github.com/denfry/mcpfabric , https://modrinth.com/mod/mcpfabric | 5 stars, MIT, 2.7k Modrinth downloads, updated last week | 26.1–26.3, Fabric + NeoForge | 50+ tools: `screenshot`, `describe_scene`, `navigate_to` (A*), `break/place_block`, `attack_entity`, `run_command`, `poll_events`. 127.0.0.1 + bearer token; op-level on by default. |
| minecraft-java-fabric-mcp-server (chapmanjw) | https://github.com/chapmanjw/minecraft-java-fabric-mcp-server | 11 stars, MIT, last commit 2026-09-19, "experimental" | 1.21.11, 26.1.1, 26.1.2, 26.2 | 183 tools (≈102 default), client entrypoint with `view_capture` PNG; companion Claude Code plugin `minecraft-java-fabric-claude-plugin`. No 26.3 build listed. |
| ModHelper-MCP (realBritakee) | https://github.com/realBritakee/minecraft-mcp | 0 stars, MIT, 7 commits | n/a | 84 tools incl. Modrinth/CurseForge search and Mineflayer automation. Too new; skip. |
- MC Modder: mcpfabric is the one that matches 26.3 (the template's version). Use it in a **dev-only**
  profile for `mc-merge` play checks ("spawn the ported mob, walk to it, screenshot, read the log"). Never
  ship it in a release, keep the token, never on a public server.

### Modrinth API
- Several MCP wrappers exist (justinscott12/modrinth-mcp, ModHelper, Glama listings; none verified in depth).
- The public REST API (`https://api.modrinth.com/v2/search?facets=...`, `/project/{id}/version`) needs no
  auth for reads. MC Modder: a 3-line curl example in `mc-merge` §3 ("pin exact versions") beats another MCP server.

### Linkie / Parchment
- Linkie: no 26.x information found. Parchment: no 26.x release found; third-party docs say it only applies
  to obfuscated versions. Both matter only for pre-26 ports (`port-a-mod`), where `minecraft-dev-mcp`'s
  `find_mapping` covers the same need.

### Minecraft Development plugin for IntelliJ
- https://github.com/minecraft-dev/MinecraftDev — Mixin inspections, but an open issue reports false errors on
  `method = "*"` with WrapOperation/ModifyExpressionValue (#2518). Fabric docs require IntelliJ 2025.3+ for 26.1.
  Not usable headless by an agent; mention for humans only.

---

## 2. Testing a mod without a human

### Fabric server GameTests + client game tests (official, in Fabric API + Loom)
- Link: https://docs.fabricmc.net/develop/automatic-testing (page is for 26.2)
- Setup: `fabricApi { configureTests { createSourceSet = true; modId = "..."; enableGameTests = true; enableClientGameTests = true; eula = true } }`
  → tests in `src/gametest/java` with their own `fabric.mod.json` (`fabric-gametest`, `fabric-client-gametest` entrypoints).
- Server tests: `@GameTest` methods with `GameTestHelper`, run as part of `build`.
- Client tests: implement `FabricClientGameTest`, get `ClientGameTestContext`; `context.worldBuilder().create()`
  for a singleplayer world, `waitForChunksRender()`, **`context.takeScreenshot(name)`**. Task `runClientGameTest`.
- CI: `ClientProductionRunTask` (`runProductionClientGameTest`) with `-Dfabric.client.gametest`, `useXVFB = true`,
  screenshots in `build/run/clientGameTest/screenshots`; GitHub Actions workaround
  `-Dfabric.client.gametest.disableNetworkSynchronizer=true`.
- Unit tests: `fabric-loader-junit` (Mixin-aware JUnit); call `SharedConstants.tryDetectVersion(); Bootstrap.bootStrap();` in `@BeforeAll`.
- Maturity: official Fabric. 26.x: yes.
- MC Modder: the single biggest gap. Add a `src/gametest` set to the GTA template's `mc/`: a client test that
  opens a void world, sends a fake `cam` message through `HostLink`, waits for chunks, takes a screenshot and
  asserts the shared-memory header (`seq` even, pose matches). That turns `host/fakehost.py` from a human-read
  PNG into an exit code. For `mc-merge`, "Done means" should require at least one server GameTest per ported mechanic.

### NeoForge GameTests
- NeoForge 26.1 docs exist; MDK via the Mod Generator (ModDevGradle 2.0.141+ for 26.1). Exact MDG GameTest task
  names for 26.x not found (**unverified**; check `./gradlew tasks`). JEI and Theurgy 26.1 releases mention
  client/server game tests in CI. MC Modder already has a NeoForge 1.21.1 GameTest note in `knowledge/`.

### mc-runtime-test + HeadlessMC (production jar, real client, CI)
- Links: https://github.com/headlesshq/mc-runtime-test (65 stars, MIT, action `@5.0.0`),
  https://github.com/headlesshq/headlessmc (407 stars, MIT; CLI launcher, `headlessmc launch fabric 26.3`).
- Does: GitHub Action that boots the real client from the built jar under Xvfb via HeadlessMC, joins a world,
  waits for chunks, quits; optional `/test runall` with
  `-DMcRuntimeGameTestMinExpectedGameTests=1` so "0 tests ran" fails.
- 26.x: 26.1–26.3 for Fabric, NeoForge, Forge. Forge/NeoForge GameTest discovery "may require additional setup";
  no-render 26.3 runs need a HeadlessMC with the SDL update. Offline accounts only for CI.
- MC Modder: the only check that tests the **shipped jar** rather than the dev run (the Bloons note already
  found dev-vs-jar differences on Forge). Add a `.github/workflows/runtime.yml` to the template.

### Mineflayer (scripted bots)
- Link: https://github.com/PrismarineJS/mineflayer — 7.6k stars, MIT. README lists up to **26.1**; 26.1.2 support
  in progress (issue/PR #2184, minecraft-data issue #1174); a third-party gist claims a 49-test pass on 26.1.2
  (**unverified**). 26.2/26.3: not found.
- Server-side only (a bot is a protocol client, sees no client rendering, and a modded server needs the mod's
  packets to be vanilla-compatible). MC Modder: useful for `mc-merge` server mechanics on a dedicated server; for
  26.3 prefer GameTests or mcpfabric.

### Screenshots / verification
- Fabric client gametest `takeScreenshot` (official), mcpfabric `screenshot`, chapmanjw `view_capture`,
  mcdev-mcp DebugBridge screenshots. MC Modder's own `FrameExporter` already gives pixel-exact frames.

---

## 3. Templates and generators
| Tool | Link | Status | 26.x | How MC Modder could use it |
|---|---|---|---|---|
| Fabric template generator (web) + **Fabric CLI** | https://fabricmc.net/develop/template/ , https://fabricmc.net/develop/cli/ | official; CLI needs Deno: `deno run https://fabricmc.net/cli init MyMod -y` | yes | `/mc-new` for a non-passthrough mod (`mc-merge`) should call `fabric init -y` instead of copying the GTA template; IntelliJ wizard templates are often stale (Fabric docs). |
| NeoForge Mod Generator / MDK | https://docs.neoforged.net/docs/gettingstarted/ | official; MDG 2.0.141, NG 7.1.21 for 26.1 | yes | Reference for the NeoForge lane of `port-a-mod`. |
| Architectury generator | https://generate.architectury.dev , docs https://docs.architectury.dev | official; docs target 26.2, Java 25, Architectury Loom 1.17+, `loom-no-remap` setup; API 21.0.x for 26.2 | yes | Only if a crossover must ship on Fabric and NeoForge. |
| Stonecutter (multi-version preprocessor) | plugin `dev.kikugie.stonecutter`, maven.kikugie.dev | 0.8.x / 0.9 betas seen on mirrors (**official repo not reached**); mods report 26.1–26.2 builds | reported yes | Only for a mod that must ship to 1.21.1 and 26.x at once (some passthrough hosts' prior projects are 1.21.1). Setup is reportedly painful. |
| Fabric datagen | https://docs.fabricmc.net/develop/data-generation/setup | official (26.2 docs): `fabricApi { configureDataGeneration() { client = true } }`, `./gradlew runDatagen`, `fabric-datagen` entrypoint → `src/main/generated` | yes | `mc-merge` content ports: generate models/recipes/lang/loot instead of hand-writing JSON (a top LLM error source: wrong paths, singular vs plural folders). |
| Minotaur (Modrinth Gradle) | https://github.com/modrinth/minotaur | 132 stars, LGPL-2.1, `2.+`, has `debugMode` dry-run and `syncBodyFrom` | README still says `uploadFile = remapJar` (no such task on non-remap Loom: use `jar`) | `publish-mod`: Minecraft row should say "Minotaur with `uploadFile = jar` on 26.x, `debugMode = true` first". |
| mc-publish (GitHub Action) | https://github.com/Kir-Antipov/mc-publish | 317 stars, MIT, `@v3.3`; a mirror lists last push June 2024 (**activity unverified**) | not stated | Alternative to Minotaur for Modrinth + CurseForge + GitHub Releases. Publishing stays the user's call. |

---

## 4. Other agent skill packs for Minecraft
### Jahrome907/minecraft-agent-skills
- Link: https://github.com/Jahrome907/minecraft-agent-skills — 176 stars, MIT, last commit **2026-10-11**
  ("Refresh Minecraft 26.3 skills and validation"). Claude Code + Codex (sync script, plugin bundle; also on skills.sh).
- 13 skills: modding (NeoForge/Fabric/Forge 1.20.1), plugin-dev, datapack, commands-scripting, multiloader
  (Architectury), **testing** (JUnit, MockBukkit, GameTests), **ci-release** (GitHub Actions, Modrinth/CurseForge),
  world-generation, resource-pack, imagegen, server-admin, worldedit-ops, essentials-ops. Bundled validators + `check` script.
- Does well: explicit version lanes ("don't copy 1.21.11 mapping, Loom plugin, remap task or Java 21 snippets into
  26.x"; Forge 1.20.1 plural data paths vs 1.21 singular), candid limits, reviewed against 26.3.
- MC Modder: don't rewrite generic modding/testing/CI knowledge; point to (or vendor, MIT, with credit) its
  `minecraft-testing`, `minecraft-ci-release`, `minecraft-resource-pack` skills and keep MC Modder focused on
  crossovers. Copy its "version lane" rule style into `mc-merge`.

### chouzz/minecraft-mod-dev
- Link: https://github.com/chouzz/minecraft-mod-dev — 20 stars, 12 commits, licence not shown, a directory says
  updated 2026-09-10 (**unverified**). Claude Code plugin; fetches live NeoForge/Fabric docs; JEI/AE2/Create
  integration guidance; Data Components, datagen, convention tags. 26.x not mentioned.
- Does well: inter-mod integration recipes. MC Modder: idea for `mc-merge` §3 (merge with a mod): a short
  "integrate through API/tags/JEI plugin" reference.

### rehan-remade/universal-modder (upstream)
- Already the base. Its knowledge notes are the best source for crossover-specific pitfalls.

### Not useful
- github/awesome-copilot "Minecraft Plugin Development": Paper/Spigot only.
- "senjuwoo minecraft-modding": listed on a skills directory, repo not found (**unverified**).

---

## 5. Common LLM failure modes and what prevents them
| Failure | Evidence | Prevention / tool |
|---|---|---|
| **Yarn / intermediary names and the old Loom setup in a 26.x project** (`fabric-loom` id, `mappings` line, `modImplementation`, `remapJar`, Java 21) | Fabric 26.1 porting docs: Yarn not available after 1.21.11, rename plugin, drop mappings, `implementation`/`jar`; Jahrome907's skill warns explicitly | A lint (grep) in `um publish check` or a Claude Code hook: fail on `id 'fabric-loom'`, `mappings `, `modImplementation`, `remapJar`, `net.minecraft.util.Identifier`-style Yarn class names (`MinecraftClient`, `ClientPlayerEntity`, `Identifier`) in a 26.x project. Plus `minecraft-dev-mcp` `find_mapping` to translate. |
| **Invented or moved APIs** (methods that don't exist, signatures from another version) | Fabric wiki "Using LLMs" (2026-05-16): models confuse versions/platforms and invent APIs; quarterly API breaks | Look up before writing: `mcdev-mcp mc_get_method` / `minecraft-dev-mcp get_minecraft_source`, or `./gradlew genSources` + grep. Compile after every slice. |
| **Mixin targets wrong or brittle** (wrong method name/descriptor, `@Local` captures, `@Redirect`/`@Overwrite` conflicts) | Fabric wiki mixin pages | `analyze_mixin` (minecraft-dev-mcp) or `modforge mixin-check`; prefer MixinExtras `@WrapOperation`/`@ModifyExpressionValue` (chain) over `@Redirect`; `@Unique` + modid-prefixed members; dev run flags `-Dmixin.debug.export=true` (`run/.mixin.out`) and `-Dmixin.dumpTargetOnFailure=true`; a client gametest so a failed injection is a red build, not a silent no-op. |
| **Client/server side mistakes** (client classes referenced from common code → dedicated server crash) | general Fabric knowledge; template already uses `splitEnvironmentSourceSets()` | Keep split source sets (compile-time guard); run a server GameTest / `runServer` once per change; mc-server-test (headlesshq) for the production server jar. |
| **Registry timing** (registering late, accessing registries before bootstrap, static init order) | `fabric-loader-junit` docs: "Not bootstrapped" error | Server GameTests catch it at boot; unit tests need `Bootstrap.bootStrap()`. |
| **Data/asset path errors** (singular vs plural folders, wrong JSON shape) | Jahrome907 notes Forge 1.20.1 plural vs 1.21 singular paths | Datagen instead of hand-written JSON; a client gametest screenshot shows missing-texture purple. |
| **"It passed" without running** | port-a-mod already has this rule | Tests that fail when 0 tests ran (`McRuntimeGameTestMinExpectedGameTests`), CI artefacts (screenshots, `latest.log`). |
| **Dev run ≠ shipped jar** | MC Modder Bloons note (Forge SRG); less so on 26.x but still class-loading/`include` differences | `runProductionClientGameTest` or mc-runtime-test on the built jar. |
| Publishing step uses stale tasks | Minotaur README `remapJar` | Fix in `publish-mod`. |

---

## Top 8 recommendations (impact / effort)
1. **Add Fabric GameTests + a client game test to the GTA template `mc/`** (`fabricApi.configureTests`, `src/gametest`,
   one client test: void world → fake `cam` → `waitForChunksRender` → `takeScreenshot` → assert the shared-memory header).
   Make "at least one GameTest per mechanic" part of `mc-merge`'s "Done means". Official, 26.x, ~1 hour. Turns the
   human-eyeballed fakehost PNG into a pass/fail.
2. **Add `minecraft-dev-mcp` (MCDxAI, MIT, 26.1+) to `mcp.json`** and tell `minecraft-bridge`/`port-a-mod` to run
   `analyze_mixin`, access-widener validation and `compare_versions` before writing or porting a mixin. 10 minutes.
   (`mcdev-mcp` is the alternative if call graphs matter more.)
3. **A 26.x stale-snippet lint** (in `um publish check` and/or a Claude Code PostToolUse hook on `*.gradle`/`*.java`):
   flag `id 'fabric-loom'`, a `mappings` line, `modImplementation`, `remapJar`, Java 21 toolchains, and common Yarn
   class names. Cheapest guard against the most common LLM error. ~1 hour.
4. **Fix the wrong references**: replace the nonexistent "`minecraft-modding-mcp`" line in
   `mod-any-game/references/engines/minecraft.md` with the real servers; in `publish-mod`, say Minotaur `uploadFile = jar`
   (not `remapJar`) on 26.x and `debugMode = true` for a dry run. 10 minutes.
5. **CI with `headlesshq/mc-runtime-test@5.0.0`** in the template: boots the built jar in a real 26.3 client under Xvfb,
   runs `/test runall` with a minimum-test-count guard; upload `latest.log` + screenshots. Tests the shipped jar. ~1 hour.
6. **Mixin hygiene in `minecraft-bridge`**: MixinExtras `@WrapOperation`/`@ModifyExpressionValue` over `@Redirect`/`@Overwrite`,
   `@Unique` + prefix, and add `-Dmixin.debug.export=true -Dmixin.dumpTargetOnFailure=true` to the template's dev
   `runs.client.vmArgs`. Matters because passthrough mods stack many renderer mixins next to Sodium/Iris users. 20 minutes.
7. **Reuse Jahrome907/minecraft-agent-skills (MIT, reviewed for 26.3 on 2026-10-11)** for generic testing, CI-release,
   resource-pack and datagen knowledge (link or vendor with credit) instead of writing it; keep MC Modder's skills about
   crossovers. Also switch `mc-merge` content ports to **Fabric datagen** and new non-passthrough projects to `fabric init -y`
   (Fabric CLI) rather than copying the GTA template. ~1–2 hours.
8. **Agent play-testing via MCP Fabric (denfry/mcpfabric, MIT, 26.1–26.3, Fabric+NeoForge)** in a dev-only profile for
   `mc-merge`: spawn/walk/screenshot/read events without a human. Medium effort and a security surface (op-level by default,
   localhost + token); never in releases. Use Mineflayer only for server-side checks up to 26.1. ModForge is a side option
   for 1.21.x → 26.x ports (young, inactive, checker only).

Sources: the links inline above; Fabric 26.1 porting docs https://docs.fabricmc.net/26.1.2/develop/porting/mappings/ ;
NeoForge 26.1 post https://neoforged.net/news/26.1release/ ; Fabric wiki https://wiki.fabricmc.net/tutorial:using_llms ,
https://wiki.fabricmc.net/tutorial:mixin_export , https://wiki.fabricmc.net/tutorial:mixin_redirectors .
