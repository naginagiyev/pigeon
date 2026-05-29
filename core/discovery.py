import json
import socket
import threading

UDP_PORT = 50001
BROADCAST_INTERVAL = 3.0
BROADCAST_ADDR = "255.255.255.255"

class DiscoveryService:
    def __init__(self, localIp, nicknameGetter, sharedFiles, peerRegistry, tcpPort=50002):
        self._localIp = localIp
        self._nicknameGetter = nicknameGetter
        self._sharedFiles = sharedFiles
        self._peerRegistry = peerRegistry
        self._tcpPort = tcpPort
        self._stopEvent = threading.Event()

    def start(self):
        tBroadcast = threading.Thread(target=self._broadcastLoop, daemon=True)
        tListener = threading.Thread(target=self._listenLoop, daemon=True)
        tBroadcast.start()
        tListener.start()

    def stop(self):
        self._stopEvent.set()
        self._sendLeaving()

    def _buildPayload(self, status=None):
        payload = {
            "nickname": self._nicknameGetter(),
            "ip": self._localIp,
            "tcp_port": self._tcpPort,
            "files": self._sharedFiles.forBroadcast(),
        }
        if status:
            payload["status"] = status
        return json.dumps(payload).encode()

    def _broadcastLoop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            while not self._stopEvent.is_set():
                try:
                    data = self._buildPayload()
                    sock.sendto(data, (BROADCAST_ADDR, UDP_PORT))
                except Exception:
                    pass
                self._stopEvent.wait(BROADCAST_INTERVAL)
        finally:
            sock.close()

    def _sendLeaving(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            data = self._buildPayload(status="leaving")
            sock.sendto(data, (BROADCAST_ADDR, UDP_PORT))
        except Exception:
            pass
        finally:
            sock.close()

    def _listenLoop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))
        sock.settimeout(1.0)
        try:
            while not self._stopEvent.is_set():
                try:
                    data, addr = sock.recvfrom(65535)
                except socket.timeout:
                    continue
                except Exception:
                    continue
                try:
                    payload = json.loads(data.decode())
                except Exception:
                    continue
                senderIp = payload.get("ip", addr[0])
                if senderIp == self._localIp:
                    continue
                if payload.get("status") == "leaving":
                    self._peerRegistry.markOffline(senderIp)
                else:
                    self._peerRegistry.updatePeer(payload)
        finally:
            sock.close()