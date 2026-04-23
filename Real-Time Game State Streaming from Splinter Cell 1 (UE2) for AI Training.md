# Real-Time Game State Streaming from Splinter Cell 1 (UE2) for AI Training

## Overview

The original *Tom Clancy's Splinter Cell* (2002) runs on Unreal Engine 2 (UE2) and ships with `UCC.exe` plus `Editor.dll`, making UnrealScript recompilation viable — a capability absent in Pandora Tomorrow. The game's mod community has demonstrated successful decompilation and recompilation of game `.u` packages using UCC and tools like UE Explorer. This gives the mod a genuine, well-supported path into the engine runtime to instrument game state.[^1][^2][^3][^4]

The root cause of the "data only flushed on exit" problem is that UE2's built-in `Log()` function writes to a buffered log file. The engine documentation confirms: "writing to the log file actually writes to a buffer which is periodically written to the log file", and that the buffer is only guaranteed to flush on normal shutdown. This is a design constraint of the log subsystem, not a general constraint on all I/O within the engine. The solution is to bypass the log entirely and use the networking stack or a platform-level IPC mechanism to stream data in real time.[^5]

***

## Why Not the Log?

Beyond the buffering problem, the log subsystem has a second limitation: there is no mechanism within UnrealScript to read the log file. Even with the `-FORCELOGFLUSH` command-line argument, which forces a flush after each log line, the data still goes to a file that must be consumed by a tail-like reader. This introduces an additional I/O round-trip and file system dependency. For high-frequency game state data (player position, velocity, AI state, stealth meter every tick), the overhead and latency are undesirable. Direct socket streaming is the correct architectural choice.[^6][^7][^5]

***

## Primary Approach: UnrealScript TcpLink

### What TcpLink Is

UE2 ships an `IpDrv` package that contains the `TcpLink` and `UdpLink` classes, which are thin UnrealScript wrappers over native (C++) Winsock sockets. `TcpLink` exposes:[^8][^9]

- `BindPort(int Port)` — bind to a local port
- `Listen()` — accept incoming connections (up to 5 simultaneous)[^8]
- `Open(IpAddr Addr)` — connect to a remote host
- `SendText(string Str)` / `SendBinary(int Count, byte B)` — send data
- `ReceivedText(string Text)` / `ReceivedLine(string Line)` / `ReceivedBinary(int Count, byte B)` — event callbacks when data arrives

The callbacks fire once per frame (per `Tick`). For outbound-only data streaming (which is the use case here), this is not a bottleneck — you call `SendText` from the mod's `Tick` function and the OS buffers the writes. The once-per-frame read limitation matters only if the external process is sending data back to the game.[^8]

**Note on `ReceivedBinary`**: there is a known bug in older UE2 builds where `ReceivedBinary` repeats incorrect data. This is fixed from UT2003 build 2175 onward. Since SC1 ships as a custom UE2 build, this needs to be validated; if it is affected, use `MODE_Text` or `MODE_Line` with JSON/CSV text payloads instead of binary.[^8]

### Confirmed Prior Art: UTAdmin (UT2004)

A concrete, working example of exactly this pattern exists for UT2004 — another UE2 title. The UTAdmin project implements a three-class mutator architecture: a main `Mutator` subclass that spawns an `APIServer` actor (which extends `TcpLink` and calls `BindPort` + `Listen`), plus a `Connection` class (also extending `TcpLink`) that is auto-spawned via `AcceptClass` for each incoming client. The server uses `Level.Game` and `Level.ControllerList` to access live game state and sends JSON-formatted responses via `SendText`. The same pattern directly applies to SC1.[^10]

UT2004 and SC1 share the same UE2 lineage; SC1 ships `IpDrv` as a package (it is part of the standard UE2 package set, which the SC1 release includes given it ships with the full compilation toolchain). The `IpDrv` package is the networking foundation.[^4][^11]

### Implementation Sketch for SC1

The data-streaming mutator architecture mirrors UTAdmin closely:

```unrealscript
// SCDataServer.uc — extends TcpLink, binds and listens
class SCDataServer extends TcpLink;

var SCDataConnection DataConn;

function Initialize(int Port)
{
    LinkMode    = MODE_Text;
    ReceiveMode = RMODE_Event;
    if (BindPort(Port, true) > 0)
        Listen();
}

event GainedChild(Actor C)
{
    Super.GainedChild(C);
    DataConn = SCDataConnection(C);
}

defaultproperties
{
    AcceptClass = class'SCDataConnection'
}
```

```unrealscript
// SCDataConnection.uc — one instance per connected consumer
class SCDataConnection extends TcpLink;

// Called from the mutator's Tick or a Timer
function SendGameState(string JsonLine)
{
    SendText(JsonLine $ Chr(10));
}
```

```unrealscript
// SCDataMutator.uc — entry point
class SCDataMutator extends Mutator;

var SCDataServer Server;

function PostBeginPlay()
{
    Super.PostBeginPlay();
    Server = Spawn(class'SCDataServer');
    if (Server != None)
        Server.Initialize(9999);
}

function Tick(float DeltaTime)
{
    local Pawn P;
    local string Line;

    if (Server == None || Server.DataConn == None)
        return;

    // Collect whatever game state is needed
    P = Level.GetLocalPlayerController().Pawn;
    if (P != None)
    {
        Line = "{\"x\":" $ P.Location.X
             $ ",\"y\":" $ P.Location.Y
             $ ",\"z\":" $ P.Location.Z
             $ ",\"dt\":" $ DeltaTime $ "}";
        Server.DataConn.SendGameState(Line);
    }
}
```

The external Python consumer simply opens a TCP connection to `localhost:9999` and reads newline-delimited JSON. Each line is one observation frame.

### Compiling the Mod

SC1 ships with `UCC.exe` and `Editor.dll` (confirmed necessary, absent in Pandora Tomorrow). The workflow is:[^4]

1. Add the package name to `EditPackages` in `SplinterCell.ini` (the equivalent of `UT2004.ini`)
2. Run `UCC.exe make` from the `System` directory[^12][^13]
3. Load the mutator at launch: `SplinterCell.exe ?Mutator=SCDataMod.SCDataMutator`

The EnhancedSC project has already validated that SC1's UnrealScript can be decompiled and recompiled at scale using UCC, which confirms the toolchain is functional.[^1][^4]

***

## Alternative 1: Named Pipes (IPC, Same Machine)

If a loopback TCP socket is undesirable (e.g., port conflicts, minimal overhead required), Windows named pipes are an option. UE2's `FWindowsPlatformNamedPipe::Create()` exists in the engine codebase, though its availability from UnrealScript — rather than from native C++ — is uncertain. If it is not exposed to script, named pipes would require a native code approach (see below).[^14][^15]

Performance ordering on Windows loopback is: raw shared memory > loopback socket > named pipes > anonymous pipes. For game-state JSON frames at 30–60 Hz, the difference between loopback TCP and named pipes is negligible.[^16]

***

## Alternative 2: External Memory Reading (No Mod Required at Compile Time)

If the mod compilation pipeline is blocked (e.g., stripped packages, missing `Editor.dll`), an alternative is to read game state from outside the process via Windows `ReadProcessMemory`. This approach:

- Requires finding the relevant memory offsets through static analysis (Ghidra/IDA) or the kind of reverse engineering demonstrated in the "Disassembly in the Dark" series on SC1[^17]
- Does not require any UnrealScript modification
- Is used by Gym Retro and similar platforms for console emulators[^18][^19]

The downside is that memory addresses can shift between game versions and after patches, requiring maintenance. For SC1, the EnhancedSC project's documentation on memory layout may provide a useful starting point.[^20][^1]

***

## Alternative 3: `-FORCELOGFLUSH` with Tail Reader

If neither socket nor memory approaches are feasible, the `-FORCELOGFLUSH` command-line flag forces the log buffer to flush after every line. The `Log()` calls in the mod then become near-real-time. An external process can `tail -f` the log file (or use `ReadDirectoryChangesW` / `inotify` depending on OS) to consume the data. This is the lowest-implementation-effort approach but adds OS-level file I/O latency and requires log parsing to filter mod output from engine noise.[^7][^6]

***

## Comparison of Approaches

| Approach | Latency | Implementation effort | Mod recompile required | Platform dependency |
|---|---|---|---|---|
| UnrealScript `TcpLink` (TCP loopback) | Low | Medium | Yes | None (cross-platform) |
| Named pipes via native UE2 API | Very low | High | Yes (or DLL injection) | Windows |
| `ReadProcessMemory` (external) | Low | High (offset discovery) | No | Windows |
| `-FORCELOGFLUSH` + file tail | Medium | Low | Yes (instrumentation) | None |
| UDP via `UdpLink` | Very low | Medium | Yes | None |

For the described use case — training an unsupervised learning model that requires a structured observation stream — the `TcpLink` TCP loopback socket approach is recommended. It is the pattern with the most prior art in the UE2 ecosystem, it requires no OS-specific APIs, and it allows the consumer to be written in any language with a standard socket API (e.g., Python's `socket` module).

***

## Prior Art Summary

| Project | Engine | Technique | Relevance |
|---|---|---|---|
| UTAdmin[^10] | UE2 (UT2004) | `TcpLink` mutator TCP API | Direct template — identical engine generation |
| UnrealCV[^21] | UE4 | Plugin socket command server | Concept analog for newer UE versions |
| ViZDoom[^22][^23] | ZDoom (Doom engine) | C++ API wrapping engine state | Reference design for AI game data pipelines |
| EnhancedSC[^20][^1][^4] | UE2 (SC1) | Full UnrealScript decompile/recompile | Confirms SC1 UCC toolchain is viable |
| getnamo/TCP-Unreal[^24] | UE4/5 | Blueprint TCP plugin | Pattern reference, not directly applicable |

***

## Practical Caveats

**`IpDrv` availability in SC1**: The SC1 `System` folder package list has not been exhaustively confirmed in publicly available sources. However, SC1 is confirmed to ship the full UCC toolchain including `Editor.dll`, and `IpDrv` is a standard UE2 package included in the UE2 Runtime. If `IpDrv` is absent from the SC1 distribution, it can potentially be copied from the UE2 Runtime or a UT2003/UT2004 installation, as the UCC binary is tied to the game but `IpDrv.dll` is a shared engine component.[^11][^4]

**`ReceivedBinary` bug**: The binary receive event is broken in some UE2 builds. Use text mode (`MODE_Line`, `SendText`) for outbound-only streaming to avoid this entirely.[^8]

**Tick rate and frame coupling**: Data is sent once per game tick. At default SC1 frame rates this is adequate for behavioral cloning data, but if sub-frame precision is needed, a timer-based approach with `SetTimer()` allows decoupling from render frames.

**Thread safety**: UnrealScript is single-threaded. All socket I/O goes through the engine's event loop. There is no concurrency issue, but it also means large payload construction in `Tick` will affect frame time.

---

## References

1. [Enhanced SC - A new major patch for Splinter Cell 1. It adds controller support to PC, restores graphical enhancements from the Xbox port, and fixes some old bugs/balancing issues. It also restores cut content, and adds new customization options, like No-HUD, changing Sam's suit, and much more!](https://www.reddit.com/r/Splintercell/comments/1k6zim5/enhanced_sc_a_new_major_patch_for_splinter_cell_1/) - Enhanced SC - A new major patch for Splinter Cell 1. It adds controller support to PC, restores grap...

2. [Tom Clancy's Splinter Cell - PCGamingWiki PCGW - bugs, fixes ...](https://www.pcgamingwiki.com/wiki/Tom_Clancy's_Splinter_Cell) - A major unofficial patch for the original Splinter Cell, fixing bugs and adding gameplay improvement...

3. [Managed to export sc1 level to unreal T3D format using by original ...](https://www.reddit.com/r/Splintercell/comments/1duf8qf/managed_to_export_sc1_level_to_unreal_t3d_format/) - UCC also allows you to decompile original source code from unreal packages (*.u) to uc files and com...

4. [Enhanced SC v1.4 is now LIVE! : r/Splintercell - Reddit](https://www.reddit.com/r/Splintercell/comments/1q0w8w8/enhanced_sc_v14_is_now_live/) - SC1 comes with UCC.exe but more importantly Editor.dll which holds all the compile functions, both a...

5. [Wikis / Unreal Wiki / Legacy:Log File](https://unrealarchive.org/wikis/unreal-wiki/Legacy:Log_File.html) - The log function takes two arguments, though the second argument is optional. The first argument is ...

6. [Anyway to force flush the logs to Launch.log?](https://forums.unrealengine.com/t/anyway-to-force-flush-the-logs-to-launch-log/149952) - Restart UDK Editor or UDK Game to rebuild logs. When you want to clean your logs run it. make your s...

7. [Useful command line arguments - Gamedev Guide](https://ikrima.dev/ue4guide/wip/useful-command-line-arguments/) - Unreal engine 4 game framework diagram for relation of all major base object types ... -FORCELOGFLUS...

8. [TcpLink - UnrealWiki](https://beyondunrealwiki.github.io/pages/tcplink.html) - An Internet TCP/IP connection. Properties ELinkState enum Methods Native function Events Note that R...

9. [All you ever wanted to know about the Master Uplink settings in Unreal](https://www.oldunreal.com/wiki/index.php?title=All_you_ever_wanted_to_know_about_the_Master_Uplink_settings_in_Unreal_-_IpServer_Package_for_Unreal_v1.0) - UdpServerUplink and UdpServerQuery are the two classes in IpServer that handle master server uplinks...

10. [UTAdmin | Sarah's Forge .Dev](https://sarahsforge.dev/blog/utadmin) - Direct game state access: Uses Level.Game and Level.ControllerList to query server state. The Protoc...

11. [Wikis / Unreal Wiki / Unreal Engine 2 Runtime](https://unrealarchive.org/wikis/unreal-wiki/Unreal_Engine_2_Runtime.html) - heh

12. [Wikis / Unreal Wiki / UCC - Unreal Archive](https://unrealarchive.org/wikis/unreal-wiki/UCC.html) - UCC is the Unreal Engine's commandline client, a raw execution enviroment (outside the game) for com...

13. [Unrealscript language and grammar for Visual Studio Code · GitHub](https://github.com/ericblade/vscode-unrealscript) - If your game project uses the 'standard' unreal 1/2/3 paths 'System/UCC.exe' and 'System/UnrealEd.ex...

14. [IPC and Pipes - Epic Developer Community Forums - Unreal Engine](https://forums.unrealengine.com/t/ipc-and-pipes/1290443) - So probably there is a way in ue to create a pattern of “Named Pipes” and use it on processes. Block...

15. [Interactive Process Communication - C++](https://forums.unrealengine.com/t/interactive-process-communication/30037) - I am trying to communicate with a process constantly. What i need: I create the process, which is an...

16. [Inter-process communication - any guidance / reading suggestions?](https://gamefaqs.gamespot.com/boards/210-game-design-and-programming/73333625) - The situation. A client wants to be able to click a link in a standalone web browser, and have that ...

17. [Reverse Engineering/Bashing Splinter Cell to See What Falls Out | DitD Episode 1](https://www.youtube.com/watch?v=1TeDlUv70ew) - I had a great time hacking away at Splinter Cell and uncovering revelation after revelation in this ...

18. [Gym Retro - OpenAI](https://openai.com/index/gym-retro/) - We're releasing the full version of Gym Retro, a platform for reinforcement learning research on gam...

19. [Application to Video Games - how to extract environment and state](https://www.reddit.com/r/reinforcementlearning/comments/pp1mb3/application_to_video_games_how_to_extract/) - I was wondering if anyone out there has any experience, sources, papers, or examples they can share ...

20. [This Incredible Splinter Cell Mod Upgrades A Stealth Classic - Kotaku](https://kotaku.com/splinter-cell-enhanced-mod-pc-steam-deck-2000616399) - Steam Deck support, however, is where this mod really shines. It runs surprisingly well for such an ...

21. [UnrealCV: Connecting Computer Vision to Unreal Engine](https://arxiv.org/pdf/1609.01326.pdf) - ...however, has spent a lot of effort creating 3D worlds, which a player
can interact with. So resea...

22. [ViZDoom: A Doom-based AI Research Platform for Visual ... - arXiv](https://arxiv.org/abs/1605.02097) - The software, called ViZDoom, is based on the classical first-person shooter video game, Doom. It al...

23. [ViZDoom/README.md at master · Farama-Foundation/ViZDoom](https://github.com/Farama-Foundation/ViZDoom/blob/master/README.md) - Reinforcement Learning environments based on the 1993 game Doom :godmode: - Farama-Foundation/ViZDoo...

24. [does this let you setup a TCP socket in an Unreal game client that ...](https://github.com/getnamo/TCP-Unreal/issues/11) - My use case is for sending data from an external app, say a web browser, through to Unreal. TLS isn'...

