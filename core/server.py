import socket
import threading

TCP_PORT = 50002
CHUNK_SIZE = 1024 * 1024

class FileServer:
    def __init__(self, sharedFiles, port=TCP_PORT):
        self._sharedFiles = sharedFiles
        self._port = port

    def start(self):
        t = threading.Thread(target=self._acceptLoop, daemon=True)
        t.start()

    def _acceptLoop(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(("", self._port))
        except OSError as e:
            raise RuntimeError(f"Port {self._port} is already in use. Close any other instance of this app.") from e
        srv.listen(10)
        srv.settimeout(1.0)
        while True:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            t = threading.Thread(target=self._handle, args=(conn,), daemon=True)
            t.start()

    def _handle(self, conn):
        try:
            line = b""
            while not line.endswith(b"\n"):
                ch = conn.recv(1)
                if not ch:
                    return
                line += ch
            line = line.decode().strip()
            parts = line.split()
            if len(parts) != 3 or parts[0] != "REQUEST":
                conn.sendall(b"ERROR bad_request\n")
                return
            fileId = parts[1]
            startByte = int(parts[2])
            entry = self._sharedFiles.getFileById(fileId)
            if entry is None:
                conn.sendall(b"ERROR file_not_found\n")
                return
            fullPath = entry["full_path"]
            totalSize = entry["size_bytes"]
            filename = entry["filename"]
            header = f"OK {totalSize} {filename}\n".encode()
            conn.sendall(header)
            with open(fullPath, "rb") as f:
                f.seek(startByte)
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    conn.sendall(chunk)
        except FileNotFoundError:
            try:
                conn.sendall(b"ERROR file_not_found\n")
            except Exception:
                pass
        except Exception:
            pass
        finally:
            conn.close()