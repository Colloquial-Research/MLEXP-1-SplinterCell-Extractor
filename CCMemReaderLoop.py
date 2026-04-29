# Query's windows process for SplinterCell.exe and prints 4-byte value from address
import win32api
import win32process
import ctypes
import time
import socket
import json

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

# Splinter Cell address
exe_name = "SplinterCell.exe"

# Simple JSON-over-TCP export
HOST = "127.0.0.1"
PORT = 65432

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print(f"Export server listening on {HOST}:{PORT}")

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

while True:
    conn = None
    try:
        conn, addr = server.accept()
        print("Client connected:", addr)

        last_value = None
        while True:
            value = read_int(h_game, 0x12345678) # Cheat Engine address
            if value is None:
                break
            
            if value != last_value:
                data = {
                    "missionValue:" value,
                    "timestamp": time.time()
                }
                msg = json.dumps(data).encode("utf-8") + b"\n"
                try:
                    conn.sendall(msg)
                except:
                    break
                last_value = value
            
            time.sleep(0.05)
    
    except Exception as e:
        print("Server error:", e)
    finally:
        if conn:
            conn.close()