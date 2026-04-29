import json
import socket
import time

from pymem import Pymem

GAME_EXE = "SplinterCell.exe" # Needs to be exact name of running process
HOST = "127.0.0.1"
PORT = 60001

def read_bytes(pm, addr, size):
    # Reads raw bytes from process at address
    return bytes(pm.read_bytes(addr, size))

def read_typed(pm, addr, fmt):
    # Read struct.pack format code
    raw = read_bytes(pm, addr, struct,calcsize(fmt))
    return struct.unpack(fmt, raw)[0]

def read_npc_list(pm):
    # Recontrust list of visible NPCs from memory
    ptr_to_array = read_typed(pm, NPC_LIST_PTR, "i")
    array_base = ptr_to_array + NPC_LIST_OFFSET

    npcs = []
    for i in range(NPC_COUNT_MAX):
        npc = {"index": i, "active": False}
        npc_addr = array_base + i * NPC_SIZE

        try:
            # Read each known field, skip non-visible or dead NPCs
            for field_name, field_offset, field_fmt in NPC_STRUCT:
                val_addr = npc_addr + field_offset
                val = read_typed(pm, val_addr, field_fmt)
                npc[field_name] = val
            
            if npc["state"] > 0 and npc["health"] > 0:
                npc["active"] = True
                npcs.append(npc)
        except Exception:
            pass
    
    return npcs

def serve_json_stream():
    # JSON-over-TCP
    pm = Pymem(GAME_EXE)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(1)

    print(f"Listening on {HOST}:{PORT} for JSON clients...")
    client_conn, addr = sock.accept()
    print(f"Client connected: {addr}")

    try:
        while True:
            try:
                npcs = read_npc_list(pm)
                data = {"timestamp": time.time(), "npcs": npcs}
                json_payload = json.dumps(data).encode("utf-8") + b"\n"
                client_conn.sendall(json_payload)
                time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                print("Client disconnected, waiting for reconnection...")
                client_conn.close()
                client_conn, addr = sock.accept()
                print(f"New client: {addr}")
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        client_conn.close()
        sock.close()
        pm.close_process()

if __name__ == "__main__":
    serve_json_stream()