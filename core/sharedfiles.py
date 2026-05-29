import os
import time
import threading
from uuid import uuid4

class SharedFiles:
    def __init__(self):
        self._lock = threading.Lock()
        self._files = []

    def addFile(self, fullPath):
        fullPath = os.path.abspath(fullPath)
        with self._lock:
            for f in self._files:
                if f["full_path"] == fullPath:
                    return None
            fileId = str(uuid4())[:8]
            entry = {
                "file_id": fileId,
                "filename": os.path.basename(fullPath),
                "full_path": fullPath,
                "size_bytes": os.path.getsize(fullPath),
                "shared_at": time.time(),
            }
            self._files.append(entry)
            return entry

    def removeFile(self, fileId):
        with self._lock:
            self._files = [f for f in self._files if f["file_id"] != fileId]

    def getFileById(self, fileId):
        with self._lock:
            for f in self._files:
                if f["file_id"] == fileId:
                    return f
        return None

    def getAll(self):
        with self._lock:
            return list(self._files)

    def forBroadcast(self):
        with self._lock:
            return [
                {
                    "file_id": f["file_id"],
                    "filename": f["filename"],
                    "size_bytes": f["size_bytes"],
                    "shared_at": f.get("shared_at", time.time()),
                }
                for f in self._files
            ]