import os
import socket
import threading

CHUNK_SIZE = 1024 * 1024

class DownloadManager:
    def __init__(self, signals):
        self._signals = signals
        self._lock = threading.Lock()
        self.downloads = {}

    def getDownload(self, fileId):
        with self._lock:
            return dict(self.downloads[fileId]) if fileId in self.downloads else None

    def startDownload(self, fileId, peerIp, tcpPort, filename, totalBytes, peerNickname="", destinationPath=None):
        partPath = None
        targetPath = destinationPath
        startByte = 0
        mode = "wb"

        with self._lock:
            existing = self.downloads.get(fileId)
            if existing and existing["status"] in ("paused", "error"):
                if os.path.exists(existing["local_path"]):
                    startByte = os.path.getsize(existing["local_path"])
                    partPath = existing["local_path"]
                    targetPath = existing.get("target_path", targetPath)
                    mode = "ab"
            if partPath is None:
                if not targetPath:
                    return
                partPath = self._resolvePartPath(targetPath)

        with self._lock:
            cancelEvent = threading.Event()
            self.downloads[fileId] = {
                "file_id": fileId,
                "filename": filename,
                "peer_ip": peerIp,
                "peer_nickname": peerNickname,
                "total_bytes": totalBytes,
                "received_bytes": startByte,
                "status": "downloading",
                "local_path": partPath,
                "target_path": targetPath,
                "cancel_event": cancelEvent,
            }

        t = threading.Thread(
            target=self._downloadThread,
            args=(fileId, peerIp, tcpPort, startByte, mode),
            daemon=True,
        )
        t.start()

    def cancelDownload(self, fileId):
        with self._lock:
            d = self.downloads.get(fileId)
            if d:
                d["cancel_event"].set()
                d["status"] = "cancelled"
                path = d.get("local_path")
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        with self._lock:
            self.downloads.pop(fileId, None)

    def _resolvePartPath(self, targetPath):
        directory = os.path.dirname(targetPath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        return targetPath + ".part"

    def _downloadThread(self, fileId, peerIp, tcpPort, startByte, mode):
        with self._lock:
            d = self.downloads.get(fileId)
            if not d:
                return
            cancelEvent = d["cancel_event"]
            localPath = d["local_path"]
            targetPath = d["target_path"]
            totalBytes = d["total_bytes"]

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((peerIp, tcpPort))
            request = f"REQUEST {fileId} {startByte}\n".encode()
            sock.sendall(request)

            header = b""
            while not header.endswith(b"\n"):
                ch = sock.recv(1)
                if not ch:
                    raise ConnectionError("Connection closed before header")
                header += ch
            header = header.decode().strip()

            if header.startswith("ERROR"):
                raise ValueError(header)

            parts = header.split(" ", 2)
            totalBytes = int(parts[1])

            with self._lock:
                if fileId in self.downloads:
                    self.downloads[fileId]["total_bytes"] = totalBytes

            sock.settimeout(30)
            with open(localPath, mode) as f:
                received = startByte
                while True:
                    if cancelEvent.is_set():
                        with self._lock:
                            if fileId in self.downloads:
                                status = self.downloads[fileId]["status"]
                                if status != "paused":
                                    self.downloads[fileId]["status"] = "paused"
                        return
                    chunk = sock.recv(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    with self._lock:
                        if fileId in self.downloads:
                            self.downloads[fileId]["received_bytes"] = received
                    self._signals.downloadProgress.emit(fileId, received)

                    if received >= totalBytes:
                        break

            with self._lock:
                d = self.downloads.get(fileId)
                if d and d["status"] == "cancelled":
                    return

            final = targetPath
            os.replace(localPath, final)
            with self._lock:
                if fileId in self.downloads:
                    self.downloads[fileId]["status"] = "complete"
                    self.downloads[fileId]["local_path"] = final
                    self.downloads[fileId]["received_bytes"] = totalBytes
            self._signals.downloadComplete.emit(fileId)

        except OSError as e:
            self._setError(fileId, f"Disk error: {e}")
        except (ConnectionResetError, ConnectionError, TimeoutError):
            self._setError(fileId, "Peer disconnected")
        except ValueError as e:
            self._setError(fileId, str(e))
        except Exception as e:
            self._setError(fileId, str(e))
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _setError(self, fileId, message):
        with self._lock:
            if fileId in self.downloads:
                self.downloads[fileId]["status"] = "error"
                self.downloads[fileId]["error_message"] = message
        self._signals.downloadError.emit(fileId, message)