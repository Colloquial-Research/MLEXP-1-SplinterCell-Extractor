import socket
import json

HOST = "127.0.0.1"
PORT = 60001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

buffer = b""
while True:
    data = sock.recv(4096)
    if not
        break
    buffer += data

    while b"\n" in buffer:
        line, buffer = buffer.split(b"\n", 1)
        try:
            msg = json.loads(line.decode("utf-8"))
            print(msg["timestamp"], "NPCs:", len(msg["npcs"]))
        except Exception as e:
            print("JSON error:", e)