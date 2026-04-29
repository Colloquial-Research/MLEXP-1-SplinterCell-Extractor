# Query's windows process for SplinterCell.exe and prints 4-byte value from address
import win32api
import win32process
import ctypes

PROCESS_VM_READ = 0x0010

exe_name = "SplinterCell.exe"
pid = None
for proc in win32process.EnumProcesses():
    try:
        h = win32api.OpenProcess(PROCESS_VM_READ | win32process.PROCESS_QUERY_INFORMATION,
                                 False, proc)
        name = win32process.GetModuleFileNameEx(h, 0)
        if exe_name.lower() in name.lower():
            pid = proc
            win32api.CloseHandle(h)
            break
        win32api.CloseHandle(h)
    except:
        pass

if not pid:
    print("Game not found.")
    exit()

h = win32api.OpenProcess(PROCESS_VM_READ, False, pid)
addr = 0x12345678
buf = (ctypes.c_char * 4)()
bytes_read = ctypes.c_size_t()

if ctypes.windll.kernel32.ReadProcessMemory(h.handle, addr, buf, 4, ctypes.byref(bytes_read)):
    value = int.from_bytes(buf.raw, "little")
    print("Value:", value)
else:
    print("Read failed.")