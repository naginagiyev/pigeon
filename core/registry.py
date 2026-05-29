import time
import threading

class PeerRegistry:
    OFFLINE_THRESHOLD = 9.0

    def __init__(self, signals):
        self._lock = threading.Lock()
        self._peers = {}
        self._signals = signals

    def updatePeer(self, data):
        ip = data.get("ip")
        if not ip:
            return
        wasOffline = False
        with self._lock:
            existing = self._peers.get(ip)
            if existing:
                wasOffline = not existing.get("online", True)
            self._peers[ip] = {
                "nickname": data.get("nickname", ip),
                "ip": ip,
                "tcp_port": data.get("tcp_port", 50002),
                "last_seen": time.time(),
                "files": data.get("files", []),
                "online": True,
            }
        self._signals.peerUpdated.emit(self.getAll())
        if wasOffline:
            self._signals.peerJoined.emit(data.get("nickname", ip), len(data.get("files", [])))

    def markOffline(self, ip):
        with self._lock:
            if ip in self._peers:
                self._peers[ip]["online"] = False
        self._signals.peerOffline.emit(ip)

    def getAll(self):
        with self._lock:
            return {ip: dict(p) for ip, p in self._peers.items()}

    def startTimeoutChecker(self):
        t = threading.Thread(target=self._timeoutLoop, daemon=True)
        t.start()

    def _timeoutLoop(self):
        while True:
            time.sleep(2)
            now = time.time()
            offlineIps = []
            with self._lock:
                for ip, peer in self._peers.items():
                    if peer.get("online") and (now - peer["last_seen"]) > self.OFFLINE_THRESHOLD:
                        offlineIps.append(ip)
            for ip in offlineIps:
                self.markOffline(ip)