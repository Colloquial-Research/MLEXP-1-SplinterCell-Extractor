// CCDataMutator.uc - entry point
class CCDataMutator extends Mutator;

var CCDataServer Server;

function PostBeginPlay()
{
   Super.PostBeginPlay();
   Server = Spawn(class'CCDataServer');
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