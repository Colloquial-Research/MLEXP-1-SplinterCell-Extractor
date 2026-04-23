// CCDataServer.uc - extends TcpLink, binds and listens
class CCDataServer extends TcpLink;

var CCDataConnection DataConn;

function Initialize(int Port)
{
   LinkMode = MODE_Text;
   ReceiveMode = RMODE_Event;
   if (BindPort(Port, true) > 0)
      Listen();
}

event GainedChild(Actor C)
{
   Super.GainedChild(C);
   DataConn = CCDataConnection(C);
}

defaultproperties
{
   AcceptedClass = class'CCDataConnection';
}