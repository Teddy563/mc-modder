# What the Minecraft passthrough projects built that MC Modder lacks

Research date 2026-10-15. Sources: each repo's README on `main`, plus SkyCraft `docs/DESIGN.md` and
`protocol/skycraft_protocol.h`, EldenCraft `PROTOCOL.md` and `docs/building.md`, Minecraft-Ring
`docs/development.md`, minecraft-crossover-bridge `docs/how-it-works.md`, ValCraft `NOTICE.md`,
the Wither Storm `mc-forge/README.md`, and file listings (blobless clones, no checkout, nothing run).
Licences come from each repo's root LICENSE file. The GitHub API hit its rate limit, so there are no
star counts here. Everything below is what the creators report. Nobody here play-tested any of it.

MC Modder baseline (local clone, unchanged): one GTA V template (`examples/minecraft-gta5-passthrough`).
- Route: frame compositing plus state.
- Guest: Fabric 26.3, package `dev.rehan.passthrough`.
- Transport: JSON over WebSocket on 127.0.0.1:25599 with no token, and a frame mapping
  `Local\MCPassthroughFrame` (magic `MCPT` v1, 3 seqlocked slots, colour + depth + overlay).
- Ownership: the host owns movement on foot. Host collision reaches Minecraft as barrier-block
  columns.
- Gameplay classes (`MobWar`, `Nether`, the `gta` relay) live in the same jar as the bridge.
- Tests: `fakehost.py`, `fakegta.cpp`, `ws_test.cpp`, `place_test.py`, `tnt_test.py`. No Java unit tests.
- Geometry transfer, collision fields, installers and ownership are covered well in
  `knowledge/techniques/*`, but only as notes. None of it is code.

## Projects

| Project | Licence | Route | MC version / loader | Transport | Camera / latency | Collision | Input owner | Install / launch | Testing |
|---|---|---|---|---|---|---|---|---|---|
| **chasmlol/SkyCraft** (Skyrim AE 1.7.104, SKSE) | MIT | Geometry transfer: SKSE draws MC meshes and atlases in Skyrim's D3D11 world pass. Hand/HUD/GUI go as up to 3 RGBA overlays | 26.3 Fabric | One mapping `Local\SkyCraft_v1`, magic `SKYC` v11. Header holds both PIDs and heartbeats. Seqlocked state slots (SkyState, McState, WaterGrid), input ring, 32 MB collision ring, 64 MB render ring, actor table, event ring. `collisionEpoch` drops data on a world change; `teleportSeq`/`teleportAck` handshake | MC owns the camera. McState sends interpolated eye pose, FOV, bob, plus the raw prev/cur 20 Hz tick positions with a QPC timestamp, so Skyrim interpolates on its own clock | Havok shapes walked on a worker. Triangles plus 1/8-block AABBs are injected into `Entity.collide` (a mixin, not blocks). Cells steeper than ~50° become walls. Guest→host: dug-cell masks, mesh cutting, NPC block collision | MC owns movement. Skyrim has focus, swallows input and forwards it; MC is hidden but "focused". Small allow-list (activate, Esc, map). "Use": nearest of the two picks wins. Furniture, mounts and scenes hand control to Skyrim | MO2/Vortex zip. A portable Prism bundle unpacks to `%LOCALAPPDATA%\SkyCraft`, starts hidden with Skyrim and quits with it. Single instance. Launched via shell, outside MO2's VFS. INI can point to your own launcher. Bundles e4mc for MP | JUnit (`SkyRayTest`, `TriColliderTest`), `fake_skyrim.py`, `fake_guest.py`, `tick_monitor.py`, `trace_motion.py`, `dump_collision.py` |
| **mrborghini/libertycraft** (GTA IV 1.0.8.0, IV-SDK ASI) | MIT, except `asi/` GPL-3.0 (IV-SDK) | Geometry transfer (D3D9) and a composited HUD | 26.3 Fabric (fork of SkyCraft's guest) | `/dev/shm` file, byte-compatible with SkyCraft v11 under its own magic | MC owns; GTA draws | Native line probes and object sampling feed SkyCraft's triangle+voxel representation (only acquisition was rewritten). Opaque depth snapshot before transparents | MC; `\` switches to Niko mode; missions, cutscenes and cars hand over to GTA | Windows `.bat`/PS and a Linux `curl \| bash` installer: SHA-256-verified release, pinned downgrade assets, backup manifest, `--uninstall`, `--dry-run`, idempotent, configures a Prism instance. CI publishes a release on every push to main | `asi/tests/*` (GPL), 13 JUnit suites, `fake_host.py`, `fake_minecraft.py` |
| **zeyvu/FalloutCraft** (FO4 1.11.240, F4SE 0.7.9) | MIT (keeps chasmlol's notice) | Geometry transfer (SkyCraft lineage) | 26.3 Fabric **and NeoForge 1.21.1 from one source** | SkyCraft protocol (same header) | as SkyCraft | Havok streamed in. Host ground re-checked every frame as a safety net. Guest blocks become greedy Havok boxes; NPCs don't path around them | MC (E is Fallout's activate, I is the MC inventory) | Release zip for MO2. MC via `gradlew runClient` or your own instance; either side can restart | Preprocessor check (`tools/preprocess.py check`); no tests seen |
| **Davozh/new-vegascraft** (FNV 1.4.0.525, xNVSE) | MIT | Frame compositing. **A fork of MC Modder's GTA V template** | 26.3 Fabric, still `dev.rehan.passthrough` | Same WebSocket on 25599 and frame layout. Native-Linux Java writes `/dev/shm`; Wine maps it as `Z:\dev\shm\...`. The 32-bit host maps only the slot it reads | Host owns. Pose is read at present time, which fixed shake | Havok rays become barrier columns (radius 32, 48 a tick). No host collision for guest blocks yet | Host; `B` toggles build mode | Shell `install.sh` / `--remove`; Proton DLL overrides | `fakehost.py`, `predict.py`, `motion.py`, F10/F11 debug views, MODLOG |
| **SocketByte/EldenCraft** (ER 2.7.1.0, me3) | MIT | **Hybrid.** Placed blocks are one baked mesh drawn natively in ER's D3D12 frame. Entities, avatar and HUD come from captured frames via **shared GPU textures** (ECGT), with CPU frames (MCPT) as fallback. Vanilla chunks are left out of the RGB-D capture only while an acknowledged mesh revision covers the view | 26.3 Fabric | About 11 named, versioned transports (MCPT, ECGT, ECHS, combat, healing, world, mesh, scene camera, chat, Nether, campaign JSON). Each has its own session identity, sequence and freshness window (150–500 ms), and checks the peer PID. Bounded strict JSON, replaced atomically. "No game pointers cross the process boundary." Spec in `PROTOCOL.md` | Scene camera channel with projection and alignment. Entities can still trail when turning | **Host owns movement and collision.** A native movement model reproduces vanilla walking, sprinting, elytra and Torrent at ER's physics stage; the capsule is clamped to 0.6 × 1.8 | MC input. R and the map go to ER. Menus become MC screens | `EldenCraft.cmd`: downloads checksum-verified portable Java, Prism, me3 and ReShade; `check` verifies files and game version; separate `EldenCraft.sl2`; verified ZIP backups (a failed backup aborts); detects ReShade conflicts; `Troubleshoot.cmd` support bundle (redacted, no upload). Reproducible builds. CI release on tag | ~50 Java `*Conformance` suites, 17 compositor CTests (protocol, projection, GPU transport), Pester launcher tests, Python frame-ABI tests |
| **siddoff/Minecraft-Ring** (ER 2.7.1.0) | MIT | Frame compositing (D3D12): GPU shared textures with a memory fallback, 4 layers, up to 4K | 1.21.1 Fabric (0.116.17) | File-backed mappings under `ERMC_DIR`, seq counters, separate regions for terrain queries, platforms, enemies, combat | MC owns. Pose captured with each frame. F8 handoff retires pending captures | Native ray mailbox (2 ms/frame budget), 12–24 m predictive prefetch, verified-air cache, moving-platform tracking every 40 ms | MC. F8 hands everything to ER and back. The loader refuses to run without the launcher marker or with EAC present | `Install.ps1` (backs up saves, moves conflicting mods aside), `Restore.ps1`. No portable release yet | ~20 `tools/test_*.py` regression harnesses (terrain, F8 handoff, platforms, crash recorder), benchmarks, `status.py` heartbeat check |
| **justbustin/minecraft-crossover-bridge** (MHW 15.23 and ER 1.17.1 on macOS CrossOver) | MIT (MinHook BSD-2) | Frame compositing | 1.21.1 Fabric, native macOS | Files in `/tmp` mapped by both macOS Java and Wine (`MAP_SHARED`): 8 MB `bridge.shm` (state, rays, entity table, damage queues, debug mailbox, seqlocks) and 80–110 MB triple-buffered `frames.shm` | MC owns. The frame's camera is published only after its pixels exist | MC asks for ray batches; the game casts them on its own thread; hits become invisible blocks | MC; F8 hands over to the game | Install script per game; ER offline launcher without EAC; `--remove` | `reload_core.sh` **hot-swaps the core DLL** behind a fixed loader whose stubs outlive the core. Every address is signature-checked and a feature turns off on mismatch. Game functions run only on the game thread. Porting checklist in `docs/how-it-works.md` |
| **LoAlCo/ValCraft** (Valheim, BepInEx C#) | **No licence** (only SkyCraft's MIT for the `fabric/` and protocol parts) | Geometry transfer | 26.3 Fabric (SkyCraft fork, renamed by `tools/rename_fork.py`) | SkyCraft layout as `valcraft_protocol.h`, mirrored in C# and Java | as SkyCraft | Valheim collision voxelised (ideas ported from SkyCraft); optional "block terrain" mode with its own save | MC; F7 back to Valheim | Thunderstore/Gale zip with BepInEx, optional WinForms installer, portable Prism bundle, own-launcher config | `fake_valheim_guest.py`, `run_guest.ps1` |
| **goonsn/Killcraft** (ULTRAKILL, BepInEx C#) | MIT | Geometry transfer (`WorldRender.cs`) and overlay | 26.3 Fabric. **Runs SkyCraft's unmodified guest jar** plus its own add-on mod compiled against `skycraft-0.1.2.jar` | SkyCraft protocol (`Link.cs`, `Proto.cs`) | as SkyCraft | Level geometry streamed ~36 blocks out; `UnitsPerBlock = 2` (a gameplay scale) | MC; F9 back to plain ULTRAKILL | Ships SkyCraft's own `SkyCraft-Minecraft.zip` (portable Prism) unchanged, with its licence. `McSave.cs` prepares the world and writes a data pack before MC starts. `FreshWorldEachLaunch` | none seen |
| **Orinkle/passthrough-mod-toolkit** | MIT (credits SkyCraft and universal-modder headers) | Scaffolder, not a mod | n/a | One `schema.yaml` (fixed container plus per-host vocabulary) → `ptgen` bindings in C++, C#, Java, Rust and Python. It round-trips the SkyCraft and FalloutCraft headers with zero structural diff | n/a | n/a | n/a | n/a | Python fake_host/fake_guest on a real mapping, testing heartbeat timeout, epoch invalidation and steep wall. `negative_control.py` turns each guard off and checks that its scenario fails. MCP server. `params.yaml` with evidence tiers. No hardware runs |
| **cyteon/GrandTheftMinecraft** (GTA V Legacy) | MIT | **Not passthrough:** Minecraft is rebuilt inside GTA (content port) | assets from MC 1.21.11 | n/a | n/a | Blocks are frozen GTA objects within `PropRadius`, capped by `MaxModObjects` (GTA pools crash near 1500); a poly renderer draws beyond that | GTA | OIV package. On first run it finds the user's 1.21.11 jar (SHA-1 checked against Mojang) or downloads it from Mojang, then builds textures and sounds locally; nothing is redistributed. CI | none seen |
| **VortexisTV/wither-storm-gta5-passthrough** | MIT (MC Modder's notice kept) | Frame compositing. **A fork of MC Modder's GTA V template** | **Forge 1.20.1** (47.4.10) to run Cracker's Wither Storm mod (compile-only dependency, not bundled); the Fabric 26.3 code is kept as reference | Same port 25599 and `Local\MCPassthroughFrame` ("only one bridge at a time") | as the template | Proxies for GTA NPCs and cars; storm grabs pull GTA entities | GTA | WSL `install.sh`; `install.ps1` updates only the ASI and FX, with backup and `-Restore` | `fakehost.py --storm 4` |

### Lineage and reuse found
- **SkyCraft's guest family:**
  - Killcraft runs the *unmodified* SkyCraft jar plus an add-on.
  - LibertyCraft, FalloutCraft and ValCraft are *forks*: renamed and changed, but on the same layout.
  - SkyCraft's guest is effectively the host-agnostic Fabric mod already, and Killcraft shows that an
    add-on on an unchanged core works.
- **MC Modder's guest family:** NewVegasCraft and Wither Storm copied the GTA V template wholesale.
  Both kept the same port and mapping name, so they can't run side by side. Neither could take the
  bridge without the GTA gameplay.
- **Elden Ring:** minecraft-crossover-bridge → Minecraft-Ring (Windows port), which inspired EldenCraft.

## What MC Modder should add (ranked)

1. **Split the guest into a host-agnostic core jar and per-host add-ons.**
   - **Core:** link, frame export, camera/player sync, input, proxies and the collision field.
   - **Add-on:** `MobWar`, `Nether`, the `gta` relay and similar gameplay.
   - Mod id, mapping name, port and units come from config or system properties, so nothing gets
     renamed by forking.
   - Proven by Killcraft (unmodified SkyCraft jar plus an add-on compiled against it) and by four
     SkyCraft forks that kept the guest and rewrote only the host.
   - Two forks of MC Modder's template already exist (NewVegasCraft, Wither Storm), each a full
     copy with a clashing port and mapping name.
   - ValCraft's `rename_fork.py` shows the cost of not doing this. ValCraft has no licence, so
     don't copy that script.
2. **A written, versioned binary protocol, with generated bindings and layout tests.**
   - **Spec:** a `PROTOCOL.md` plus one header.
   - **Header fields:** magic, version, byte order, both PIDs, heartbeats, a session/epoch per
     channel, and seqlocked state slots.
   - **Channels:** SPSC event rings, bounded byte rings for collision and meshes, and freshness
     windows.
   - Keep JSON over WebSocket for director/commands only, and add a token.
   - Models: SkyCraft's header (v11, MIT, copyable with its notice) and EldenCraft's `PROTOCOL.md`
     (session identity, freshness, ack'd cumulative sequences, "no game pointers cross").
   - **Codegen:** reuse Orinkle's `ptgen` (MIT). It already produces C++, C#, Java, Rust and Python
     from a schema and round-trips SkyCraft's header with zero structural diff.
   - Why: the knowledge notes already list the bugs this prevents (layout drift, a seqlock that
     isn't one, mismatch-overwrite, a blocking WebSocket send on the game thread in NewVegasCraft).
3. **A guest-owns-movement mode with a collision field.** MC Modder only has host-owns movement
   with barrier columns.
   - Inject host triangles and 1/8-block AABBs into `Entity.collide` with a mixin (SkyCraft's
     `EntityCollideMixin`, `TriColliderTest`).
   - Mark "known empty" apart from "not received yet", and drop data on `collisionEpoch`.
   - Send prev/cur tick positions with a timestamp so the host interpolates (SkyCraft McState).
   - Add a full input bridge: host keeps focus, MC is hidden but "focused", an allow-list of host
     keys, nearest-target "use" arbitration. Add puppet hand-back flags (menu, loading, furniture,
     vehicles).
   - Used by SkyCraft, LibertyCraft, FalloutCraft, ValCraft, Killcraft, Minecraft-Ring and the
     CrossOver bridge, which makes it the dominant design.
   - Keep host-owns as the other mode: EldenCraft shows it scales, with a native movement model
     and host collision authoritative.
4. **A geometry-transfer exporter in the core**, next to frame compositing.
   - Export section meshes, atlas updates, block lights, solid and dug bitsets, held items and
     outlines through Minecraft's own mesh builders. Give it a per-frame budget (SkyCraft: 12
     sections, ~3 ms) and a bounded ring.
   - Go hybrid like EldenCraft: blocks as meshes; entities, avatar and HUD as frames. Leave vanilla
     chunks out of the capture only while an acknowledged mesh revision covers the view, so nothing
     is drawn twice or missing. Add a plane mask so the host asks only for the layers it uses.
   - Proven by SkyCraft, LibertyCraft, FalloutCraft, ValCraft, Killcraft and EldenCraft. MC Modder
     currently has notes only (`geometry-transfer-host-draws-guest-meshes.md`).
5. **A launcher/installer template.**
   - **Minecraft side:** a portable Prism instance that starts hidden with the host, quits with it,
     allows one instance only, starts outside MO2's VFS, and has an "own launcher" override
     (SkyCraft, ValCraft, Killcraft).
     - Licence: Prism is GPL-3.0. Download it pinned with SHA-256 at install or package time (as
       EldenCraft and ValCraft do) instead of committing it to the MIT repo.
   - **Host side:** idempotent install with a backup manifest, `--uninstall` and `--dry-run`
     (LibertyCraft, MIT; write it fresh); `check` for the game executable version; a separate host
     save plus verified backups, where a failed backup aborts (EldenCraft `EldenCraft.sl2`).
   - **Support and release:** a redacted support bundle (EldenCraft `Troubleshoot.cmd`); a CI
     release on tag with a `.sha256` (LibertyCraft, EldenCraft, GrandTheftMinecraft).
   - MC Modder's install scripts are GTA-only and the Minecraft side is manual.
6. **A test harness per protocol, not per host.**
   - Ship a fake host and a fake guest that speak the real protocol. Then the host plugin can be
     tested without Minecraft, and the guest without the game. SkyCraft (`fake_skyrim.py`,
     `fake_guest.py`) and LibertyCraft (`fake_host.py`, `fake_minecraft.py`) both have the pair;
     MC Modder has only the fake host.
   - Add Orinkle's scenarios (heartbeat timeout, epoch invalidation, steep wall) and its negative
     controls, which turn each guard off and check that its scenario fails.
   - Add Java conformance tests for the protocol and gameplay rules (EldenCraft has ~50, LibertyCraft
     13), compositor projection/protocol unit tests (EldenCraft CTest), and terrain regression
     harnesses (Minecraft-Ring).
   - LibertyCraft's `asi/tests` are GPL-3.0: take the idea, not the code.
   - Also test hiding the stale guest image when host menus open. That is gotcha 5 in MC Modder's
     own frame-compositing note, still unbuilt.
7. **A host-plugin skeleton with a hot-reload core and signature gates.**
   - A tiny fixed loader (`dinput8`/ASI) plus a core DLL rebuilt and swapped while the game runs.
     Hooks go through stubs that outlive the core.
   - Every address is byte-signature checked, and a feature turns off on mismatch.
   - Game functions are called only on the game thread.
   - The loader refuses to start without a launcher marker or with anti-cheat present.
   - Sources: minecraft-crossover-bridge (MIT; MinHook BSD-2 is MIT-compatible with its notice),
     Minecraft-Ring, and EldenCraft `native/loader`. Add crossover-bridge's six-row porting
     checklist (frame hook, camera, raycast, actor list and damage, stand-in, Present + depth) to
     `host-adapters`.
8. **Multi-version guest builds** from one source: Fabric 26.3, NeoForge 1.21.1 and Forge 1.20.1.
   - FalloutCraft's preprocessor (`//#if MC_1_21_1`, `gradle/preprocess.gradle`, `tools/preprocess.py`,
     MIT) builds both from one tree and lets players bring modpacks (Superb Warfare, GeckoLib).
   - Wither Storm had to port the bridge to Forge 1.20.1 by hand to run a content mod, and
     Minecraft-Ring and the CrossOver bridge target 1.21.1.
   - `minecraft-bridge/SKILL.md` says "port the mixins by reading the renderer"; this gives a
     mechanism.
9. **Generic actor proxies and receipted damage.**
   - A host actor table (id + generation, box, HP fraction, flags) becomes invisible `LivingEntity`
     proxies (SkyCraft ActorTable / `ProxySync`).
   - Hits go back as `HitActor` with the unit in the message. Host damage comes in as increasing
     `damage_events` that Minecraft acknowledges (EldenCraft), so nothing is applied twice across
     restarts.
   - MC Modder's proxies are GTA-specific code in `WorldBridge`.
10. **Key guest data by host world and cell.**
    - Carry `worldId` and an epoch in the state, and give each interior its own slot. FalloutCraft
      fixed SkyCraft's "blocks leak between interiors".
    - Optional save coupling: SkyCraft's designed `saveId` snapshot, or EldenCraft's two-save
      purchase journal.
11. **A GPU shared-texture frame path** with the CPU path kept as fallback (EldenCraft ECGT, Minecraft-Ring).
    - Only for same-GPU Windows hosts on D3D11/12. The CPU copy stays necessary across Wine/CrossOver
      and two GPUs (NewVegasCraft, the CrossOver bridge).
12. **Low priority:** shared-guest multiplayer through e4mc (SkyCraft, ValCraft), Discord presence,
    and building assets from the user's own jar with SHA-1 checks against Mojang (GrandTheftMinecraft;
    this is for content-port routes, so MC Modder already covers it as pattern 1).

## Licence notes for an MIT project
- **Copyable with the copyright notice kept:**
  - SkyCraft (guest mod, protocol header, tools, fake stand-ins);
  - LibertyCraft outside `asi/`;
  - FalloutCraft (including the preprocessor);
  - NewVegasCraft and Wither Storm (both already derived from MC Modder);
  - EldenCraft, Minecraft-Ring, minecraft-crossover-bridge (MinHook stays BSD-2);
  - Killcraft, Orinkle's toolkit (`ptgen`, stubs), GrandTheftMinecraft.
- **Do not copy:**
  - LibertyCraft `asi/` (GPL-3.0 via IV-SDK, tests included);
  - anything in ValCraft beyond what SkyCraft itself provides (no licence, so all rights reserved;
    Orinkle also refused to emit its header);
  - Prism Launcher binaries in the repo (GPL-3.0; download them unmodified at install time instead).
- **Third-party pieces keep their own licences:** CommonLibSSE-NG and CommonLibF4 templates,
  fromsoftware-rs, me3, ReShade, ScriptHookV, and Cracker's Wither Storm (never bundled).
- **Never link** TerminusBoulder/Universal-Game-Mashup-Studio, TileTrackWarehouse/Passthrough-Mod-Forge
  or StuccoWhisper/Extreme-Injector-V4. They weren't opened for this research; MC Modder's
  `tools/mc_check.py` already blocks them.
