# Safety rules

Adds the Mineplus rules to `skills/mod-any-game/references/safety.md`. Read both.
None of this is legal advice.

## Online games and anti-cheat
- Offline single-player, or Minecraft servers the user runs. Never inject into an online client.
- Kernel or user-mode anti-cheat (EasyAntiCheat, BattlEye, Vanguard, Ricochet and the rest) is a stop sign
  for code injection. Allowed: an official offline mode that ships without it. Elden Ring launched offline
  through `me3`/ModEngine2 with EAC off is the community norm; GTA V story mode with `-nobattleye` is how
  the GTA V template runs.
- Never disable or bypass anti-cheat, spoof hardware IDs, or tamper with DRM. If a loader needs the EXE
  patched past DRM, stop.
- Never automate clicks on a host's landing page while someone is at the keyboard. In the GTA V build, a
  script clicked Story Mode while the user typed elsewhere and the keystrokes reached GTA Online's
  "altered version" check. Pick the offline mode by hand.
- Refuse aimbots, ESP, speed hacks and anything that gives an edge over other players, however it is framed.

## Ownership and redistribution
- Every player supplies their own copy of both games. Don't download game files.
- Don't publish game files, Minecraft jars, extracted assets, decompiled source or retail offsets baked
  into shipped code. Publish code, patches and converters that run on the user's own install.
- Minecraft assets (textures, the font) are Mojang's. Read them from the user's own client jar at runtime,
  never commit them. The GTA V template's `video/titles.py` does this for the Minecraft font.
- Loaders (ScriptHookV, SKSE, F4SE, xNVSE, RED4ext, me3, ReShade) are fetched from their own sites by
  install scripts, never bundled.

## Mineplus rules
- **Never link, fork or recommend these repos.** They are suspected malware lures dressed up as mashup
  tools: `TerminusBoulder/Universal-Game-Mashup-Studio`, `TileTrackWarehouse/Passthrough-Mod-Forge`,
  `StuccoWhisper/Extreme-Injector-V4`. `tools/mineplus_check.py` fails if any of them appears in the toolkit.
- A viral mod's "download" is often malware. Only run loaders and mods from their official repositories
  and releases, and read install scripts before running them.
- Never re-host other people's mod builds or videos. Link to the creator's own release or post.
- Credit every project you build on, by name and link, in the README and the release post. Say honestly
  that the mod was AI-built and what was verified in the real game.

## The user's machine
- Back up saves and the game folder's loader files before any modded launch; write the restore command
  into `MODLOG.md`.
- Proxy DLLs and loaders (`dinput8.dll`, `dxgi.dll`, `version.dll`) go in the game folder: list what you add
  and ship an uninstall that removes exactly that (the GTA V template's `install.sh --remove`).
- Give the passthrough Minecraft its own launcher profile and game directory. The bridge changes options and
  creates its own world.
- Bind every bridge to `127.0.0.1`. The GTA V template's link has no token, so any local program can send it
  commands: close Minecraft when done, and add a token before shipping a new bridge.
- Stop processes by exact PID, never by name pattern.

## When to stop and ask
- The idea touches an online mode or anything with anti-cheat.
- The only route bypasses a protection.
- A step would overwrite saves or game files without a backup.
- Publishing or submitting anything: always the user's call.
