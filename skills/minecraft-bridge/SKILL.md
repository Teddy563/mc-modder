---
name: minecraft-bridge
description: The Minecraft (Fabric) half of a passthrough mod - the 127.0.0.1 link the host game talks to, the colour/depth/overlay frame export through shared memory, camera and ground sync, and the coordinate contract. Use when building or changing the Minecraft side of "Minecraft inside another game", or when writing a new host plugin that has to speak to it.
---

# The Minecraft bridge

Every passthrough has the same Minecraft half. Reuse it from `examples/minecraft-gta5-passthrough/mc/` (Fabric,
Minecraft 26.3, Java 25) instead of writing a new one. Only the gameplay classes are host-specific.

## What the Fabric mod does
| Class (`dev.rehan.passthrough`) | Job | Host-specific? |
|---|---|---|
| `client/HostLink` | WebSocket server on `127.0.0.1:25599` (`-Dpassthrough.port`) | no |
| `client/HostState`, `client/PlayerSync`, `client/mixin/CameraMixin` | render from the host's camera; Steve stands on the host player's feet | no |
| `client/FrameExporter`, `client/SharedMemory` | world colour + depth and a hand/HUD overlay into `Local\MCPassthroughFrame` | no |
| `client/ClientInput` | mouse buttons, wheel, hotbar forwarded from the host (the host keeps focus) | no |
| `client/mixin/FogRendererMixin` and friends | no sky, fog, clouds, bobbing; keeps rendering unfocused | no |
| `WorldBridge` | ground columns → barrier blocks, block sync, explosions, projectiles | ground: no; the rest: partly |
| `MobWar`, `Nether` | GTA's mobs-vs-police and Nether features | yes: delete or rewrite per host |

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

## Building it
- Minecraft 26.x ships without obfuscation: use Loom's non-remapping plugin `net.fabricmc.fabric-loom` and no
  `mappings` line. If Gradle asks for Yarn or Intermediary, it's on the old `fabric-loom` plugin.
- JDK 25. `cd mc && ./gradlew build` → `build/libs/passthrough-0.1.0.jar`.
- Give it its own launcher profile and game directory: it changes options and opens a void world called
  `passthrough` by itself.
- To rename it for a new project, change `fabric.mod.json` `id`, the package, the shared-memory name and the
  port together, and the host plugin to match. Two bridges on one PC must not share the mapping name or port.

## Older Minecraft versions
Some hosts' prior projects use Minecraft 1.21.1 (Fabric or NeoForge) or 1.20.1 Forge (Wither Storm × GTA V,
to run an existing content mod). The protocol and frame layout carry over; the mixins don't. Port the mixins
by reading the target version's renderer, not by guessing names.

## Testing without the host
1. Start Minecraft with the mod.
2. `python host/fakehost.py 10` (Windows Python with `websockets`, `numpy`, `Pillow`) flies the camera
   round test blocks over a flat ground and composites the frames over a synthetic scene. The PNGs show
   whether alignment and occlusion are right.
3. `host/place_test.py` and `host/tnt_test.py` check block sync and explosion events.
