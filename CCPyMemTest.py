import pymem
import pymem.exception

# Attach to game process (may require admin access)
try:
   pm = pymem.Pymem("SplinterCell.exe")
   # Check process id
   print('Process id: %s' % pm.process_id)
except pymem.exception.ProcessNotFound:
   print("Game not found. Run Splinter Cell first.")
   exit(1)

'''# Find addresses with Cheat Engine
module = pymem.process.module_from_name(pm.process_handle, "SplinterCell.exe")
X_OFFSET = 0x057D60D4
Y_OFFSET = 0x057D60D8
Z_OFFSET = 0x057D60DC

print("Monitoring player location (Ctrl+C to stop)...")

try:
   while True:
      try:
         x = struct.unpack('f', pm.read_bytes(X_OFFSET, 4))[0]
         y = struct.unpack('f', pm.read_bytes(Y_OFFSET, 4))[0]
         z = struct.unpack('f', pm.read_bytes(Z_OFFSET, 4))[0]
         print(f"Player Position: x={x:.2f}, Y={y:.2f}, Z={z:.2f}")
      except:
         print("Failed to read memory. Check addresses.")
      time.sleep(1)
except KeyboardInterrupt:
   print("Stopped.")'''

pm.close_process()