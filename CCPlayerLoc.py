import pymem
import pymem.process
import time
import struct

# Attach to game process (may require admin access)
try:
   pm = pymem.Pymem("SplinterCell.exe")
   # Check process id
   print('Process id: %s' % pm.process_id)
except pymem.exception.ProcessNotFound:
   print("Game not found. Run Splinter Cell first.")
   exit(1)

# Find addresses with Cheat Engine
module = pymem.process.module_from_name(pm.process_handle, "SplinterCell.exe")
player_base = module.lpBaseOfDll + 0xDEADBEEF   # Replace with real offset (e.g. CE pointer scan)
X_OFFSET = 0x00
Y_OFFSET = 0x04
Z_OFFSET = 0x08

print("Monitoring player location (Ctrl+C to stop)...")

try:
   while True:
      try:
         x = struct.unpack('f', pm.read_bytes(player_base + X_OFFSET, 4))[0]
         y = struct.unpack('f', pm.read_bytes(player_base + Y_OFFSET, 4))[0]
         z = struct.unpack('f', pm.read_bytes(player_base + Y_OFFSET, 4))[0]
         print(f"Player Position: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
      except:
         print("Failed to read memory. Check addresses.")
      time.sleep(1)
except KeyboardInterrupt:
   print("Stopped.")

pm.close_process()