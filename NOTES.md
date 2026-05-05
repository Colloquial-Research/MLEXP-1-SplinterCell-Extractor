TOM CLANCY'S SPLINTER CELL (2002) v1.3
ENHANCED SC v1.4b

TCP LOOPBACK WITH LENGTH-PREFIXED FRAMING
4-byte big-endian length prefix followed by payload. Python's socket module and any C++ networking lib on the UE side can both emit this trivially. Loopback round-trip on Windows with TCP_NODELAY set is typically 50–200μs, well inside a 60fps frame budget. Easiest to debug (Wireshark, nc), and if you ever want to offload the ML process to a second machine you change one hostname.

PAYLOAD FORMAT: MESSAGEPACK
MessagePack is the default: binary, dynamically typed, libraries on both sides (msgpack-python, msgpack-c/msgpack-cxx), roughly 3–10x smaller and faster than JSON with almost no schema friction. Protobuf is the alternative when you want the schema enforced at build time across both languages; heavier toolchain (codegen step) but it catches contract drift compile-time rather than runtime. JSON is fine for the first 48 hours of prototyping; it will be the first thing replaced.

TCP Loopback => JSON

# GET PLAYER POS; GET OBJECTIVE POS

ENGINE>EPlayerInfo.uc>PosX, PosY
PlayercalcEye> EyeLocation, EyeRotation

`GetCurrentMapName()`

EPlayerController.uc
`24> var String CurrentGoal;
 25> var String CurrentGoalSection;
 26> var String CurrentGoalKey;
 27> var String CurrentGoalPackage;
 28> var bool bNewGoal;
 29> var bool bNewNote;`

`if bNewGoal != CurrentGoal
   return bNewGoal(vector(PosX, PosY))`

`EPlayerController.uc>1896>ShowNavPoints()`
`EPlayerController.uc>2463>PlayerCalcView()`

EPlayerInfo.uc
`33> var int   PosX;
 34> var int   PosY;`

PlayerController.uc
`33> var int bGlobalXPos;
 34> var int bGlobalYPos;`

'GetLocation/SetLocation' = vector

EPattern.uc
`1984> function AddGoal(name ID,
 ...
 1993> optional string ShortPackage)`

## Engine

### Actor.uc

**Gets current map/level name:"** '1102> native (1419) final funciton string GetCurrentMapName();'

### EPlayerStats.uc

**Unreal time:** '88> funciton Tick(float DeltaTime)'

<-------------------- | -------------------->

# DATA VARIABLES:

# CORE:

### TIME.UC

"Unreal time is exposed as a long (a 64-bit signed quanity) and is defined as nnaoseconds elapsed since midnight, Jan 1, 1970

# ENGINE:

### ACTOR.UC

**Returns visible actors:**
'1371> native(312) final iterator function VisibleCollidingActors (class<actor> BaseClass, out actor Actor, float Radius, optional vector Loc, optional bool BIgnoreHiden);'

### CONTROLLER.UC

**Native funciton return true if line of sight visible (does not check for visiblity):** '120> native(514) final function bool LineOfSightTo(actor Other);'

**Native function returns true for visiblity with peripheral vision check:** '124> native(533) final funciton bool CanSee(Pawn Other);

### ECHELONENUMS.UC

'22> enum GoalStatus{...};'
'31> enum GoalType{...};'

### LEVELINFO.UC

**Current level name, unique:** `101> var() localized string Title;`
**Viewport vectors:** `126> var() vector CameraLocationDynamic;
127> var() vector CameraLocationTop;
128> var() vector CameraLocationFront;
129> var() vector CameraLocationSide;
130> var() rotator CameraRotationDynamic;`

ECHELON>CLASSES>EPATTERN.UC
**Current
**Goal priority:\*\* '1986> optional int iGoalPriority,'

- Player starting pos(x, y, z)
- Goal finish pos(x, y, z)

```

```
