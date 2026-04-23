// CCDataConnection.uc - one instance per connected consumer
class CCDataConnection extends TcpLink;

// Called from the mutator's Tick or a Timer
function SendGameState(string JsonLine)
{
   SendText(JsonLine $ Chr(10));
}