import socket, struct, msgpack

class GameConnection:
   def __init__(self, host="127.0.0.1", port=7777):
      self.sock = socket.create_connection((host, port))
      self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      self.unpacker = msgpack.Unpacker(raw=False)

   def recv_frame(self):
      header = self._recv_exact(4)
      (length,) = struct.unpack(">I", header)
      return self._recv_exact(length)

   def send_frame(self, payload: bytes):
      self.sock.sendall(struct.pack(">I", len(payload)) + payload)

   def _recv_exact(self, n):
      buf = bytearray()
      while len(buf) < n:
         chunk = self.sock.recv(n - len(buf))
         if not chunk:
               raise ConnectionError
         buf.extend(chunk)
      return bytes(buf)

   def step(self, action: dict) -> dict:
      self.send_frame(msgpack.packb(action))
      return msgpack.unpackb(self.recv_frame(), raw=False)

"""
Should be Controller != Player && bIsSeen = true;
   print(Actor.Owner)

   / bool m_bIfDirectLineOfSight
"""