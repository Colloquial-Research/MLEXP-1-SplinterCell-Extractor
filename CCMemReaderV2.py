# Query's windows process for SplinterCell.exe and prints 4-byte value from address
import win32api
import win32process
import ctypes

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

def find_process_id(exe_name):
    # Find PID by executable name.
    for pid in win32process.EnumProcesses():
        try:
            h = win32api.OpenProcess(
                PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                False,
                pid
            )
            name = win32process.GetModuleFileNameEx(h, 0)
            win32api.CloseHandle(h)
            if exe_name.lower() in name.lower():
                return pid
        except:
            pass
    return None

def read_int(h_process, address, size=4):
    # Read integer from memory
    buf = (ctypes.c_char * size)()
    bytes_read = ctypes.c_size_t()
    success = ctypes.windll.kernel32.ReadProcessMemory(
        int(h_process),
        address,
        buf,
        size,
        ctypes.byref(bytes_read)
    )
    if success:
        return int.from_bytes(buf.raw, "little")
    return None

# Splinter Cell address
exe_name = "SplinterCell.exe"
pid = find_process_id(exe_name)

if not pid:
    print("SplinterCell.exe not running.")
    exit()

h = win32api.OpenProcess(PROCESS_VM_READ, False, pid)

# Cheat Engine address
addr = 0x12345678 # example: mission objective index

value = read_int(h, addr)
if value is not None:
    print(f"Value at {hex(addr)}: {value}")
else:
    print("Read failed.")

win32api.CloseHandle(h)