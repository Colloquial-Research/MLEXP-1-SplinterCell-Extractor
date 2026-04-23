//=============================================================================
// Data Extract
//=============================================================================
class CCExtract extends Console;

event bool KeyEvent(EInputKey Key, EInputAction Action, FLOAT Delta)
{
   if (Action != IST_PRESS)
   {
      return false;
   }
   else if (Key == IK_F4)
   {
      ConsoleCommand(-LOG);
   }
}