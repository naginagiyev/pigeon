import time
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton

def _formatSize(sizeBytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if sizeBytes < 1024:
            return f"{sizeBytes:.1f} {unit}"
        sizeBytes /= 1024
    return f"{sizeBytes:.1f} PB"

def _formatTime(ts):
    delta = int(time.time() - ts)
    if delta < 60:
        return "just now"
    if delta < 3600:
        return f"{delta // 60} min ago"
    if delta < 86400:
        return f"{delta // 3600}h ago"
    return time.strftime("%b %d", time.localtime(ts))

class FileRow(QWidget):
    def __init__(self, peerNickname, fileInfo, sharedAt,
                 downloadManager, onDownload, onCancel, onRemoveShare, rowRegistry, isLocal=False, parent=None):
        super().__init__(parent)
        self._fileId = fileInfo["file_id"]
        self._onDownload = onDownload
        self._onCancel = onCancel
        self._onRemoveShare = onRemoveShare
        self._isLocal = isLocal
        self._fileInfo = fileInfo

        if rowRegistry is not None:
            rowRegistry[self._fileId] = self

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 6, 10, 6)
        outer.setSpacing(3)

        top = QHBoxLayout()
        top.setSpacing(0)

        userLabel = QLabel(peerNickname)
        userLabel.setStyleSheet("color: #9E9E9E; font-size: 11px;")
        top.addWidget(userLabel)

        top.addStretch()

        timeLabel = QLabel(_formatTime(sharedAt))
        timeLabel.setStyleSheet("color: #BDBDBD; font-size: 10px;")
        top.addWidget(timeLabel)

        outer.addLayout(top)

        bottom = QHBoxLayout()
        bottom.setSpacing(4)

        nameLabel = QLabel(fileInfo["filename"])
        nameLabel.setToolTip(fileInfo["filename"])
        nameLabel.setMaximumWidth(120)
        elided = nameLabel.fontMetrics().elidedText(
            fileInfo["filename"], Qt.TextElideMode.ElideRight, 120
        )
        nameLabel.setText(elided)
        nameLabel.setStyleSheet("font-weight: 600;")
        bottom.addWidget(nameLabel)

        bottom.addStretch()

        sizeLabel = QLabel(_formatSize(fileInfo["size_bytes"]))
        sizeLabel.setStyleSheet("color: #9E9E9E; font-size: 11px;")
        bottom.addWidget(sizeLabel)

        self._pctLabel = QLabel("")
        self._pctLabel.setStyleSheet("font-size: 11px; min-width: 36px;")
        self._pctLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._pctLabel.setVisible(False)
        bottom.addWidget(self._pctLabel)

        self._dlBtn = QPushButton("↓")
        self._dlBtn.setFixedSize(QSize(28, 28))
        self._dlBtn.setToolTip("Download")
        bottom.addWidget(self._dlBtn)

        self._cancelBtn = QPushButton("✕")
        self._cancelBtn.setFixedSize(QSize(22, 22))
        self._cancelBtn.setStyleSheet("color: #F44336; font-size: 10px;")
        self._cancelBtn.setToolTip("Cancel")
        self._cancelBtn.setVisible(False)
        self._cancelBtn.clicked.connect(lambda: self._onCancel(self._fileId))
        bottom.addWidget(self._cancelBtn)

        outer.addLayout(bottom)

        if self._isLocal:
            self._dlBtn.setVisible(False)
            self._cancelBtn.setToolTip("Stop sharing")
            self._cancelBtn.setVisible(True)
            try:
                self._cancelBtn.clicked.disconnect()
            except Exception:
                pass
            self._cancelBtn.clicked.connect(lambda: self._onRemoveShare(self._fileId))
            return

        dl = downloadManager.getDownload(self._fileId) if downloadManager else None
        if dl:
            self._applyStatus(dl["status"], dl["received_bytes"], dl["total_bytes"], fileInfo)
        else:
            self._setDownloadAction("↓", "Download")

    def _applyStatus(self, status, received, total, fileInfo):
        pct = int(received / total * 100) if total > 0 else 0

        if status == "downloading":
            self._dlBtn.setVisible(False)
            self._pctLabel.setText(f"{pct}%")
            self._pctLabel.setVisible(True)
            self._cancelBtn.setVisible(True)
        elif status == "paused":
            self._setDownloadAction("↓", "Resume download", resume=True)
            self._pctLabel.setText(f"{pct}%")
            self._pctLabel.setStyleSheet("font-size: 11px; min-width: 36px; color: #9E9E9E;")
            self._pctLabel.setVisible(True)
            self._cancelBtn.setVisible(True)
        elif status == "error":
            self._setDownloadAction("↓", "Retry download", resume=True)
            self._pctLabel.setText("ERR")
            self._pctLabel.setStyleSheet("font-size: 11px; min-width: 36px; color: #F44336;")
            self._pctLabel.setVisible(True)
        elif status == "complete":
            self._setDownloadAction("↓", "Download again")
            self._pctLabel.setVisible(False)
            self._cancelBtn.setVisible(False)

    def setProgress(self, received, total):
        pct = int(received / total * 100) if total > 0 else 0
        self._dlBtn.setVisible(False)
        self._pctLabel.setText(f"{pct}%")
        self._pctLabel.setVisible(True)
        self._cancelBtn.setVisible(True)

    def _setDownloadAction(self, text, tooltip, resume=False):
        try:
            self._dlBtn.clicked.disconnect()
        except Exception:
            pass
        self._dlBtn.setVisible(True)
        self._dlBtn.setEnabled(True)
        self._dlBtn.setText(text)
        self._dlBtn.setToolTip(tooltip)
        self._dlBtn.clicked.connect(lambda: self._onDownload(self._fileInfo, resume=resume))

class LeftPanel(QWidget):
    def __init__(self, downloadManager, onDownload, onCancel, onRemoveShare, parent=None):
        super().__init__(parent)
        self._downloadManager = downloadManager
        self._onDownload = onDownload
        self._onCancel = onCancel
        self._onRemoveShare = onRemoveShare
        self._fileRows = {}
        self.setFixedWidth(290)
        self.setObjectName("leftPanel")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._emptyLabel = QLabel("It is silence here...")
        self._emptyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emptyLabel.setStyleSheet("color: #9E9E9E;")
        outer.addWidget(self._emptyLabel, stretch=1)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setVisible(False)
        outer.addWidget(self._scroll, stretch=1)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
        self._scroll.setWidget(self._container)

    def showEvent(self, event):
        super().showEvent(event)
        bg = self.palette().color(QPalette.ColorRole.Window)
        p = self._scroll.viewport().palette()
        p.setColor(QPalette.ColorRole.Base, bg)
        p.setColor(QPalette.ColorRole.Window, bg)
        self._scroll.viewport().setPalette(p)
        self._scroll.viewport().setAutoFillBackground(True)
        self._container.setPalette(p)
        self._container.setAutoFillBackground(True)

    def refresh(self, peers, localIp, localFiles=None, localNickname="User"):
        self._fileRows.clear()
        i = 0
        while i < self._layout.count():
            item = self._layout.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                self._layout.takeAt(i)
                widget.deleteLater()
            else:
                i += 1

        allFiles = []
        for peer in peers.values():
            if peer["ip"] == localIp:
                continue
            for f in peer.get("files", []):
                sharedAt = f.get("shared_at", peer.get("last_seen", 0))
                allFiles.append((peer, f, False, sharedAt))

        for f in (localFiles or []):
            sharedAt = f.get("shared_at", time.time())
            allFiles.append((
                {"nickname": localNickname, "last_seen": sharedAt},
                f,
                True,
                sharedAt,
            ))

        allFiles.sort(key=lambda x: x[3], reverse=True)

        if not allFiles:
            self._emptyLabel.setVisible(True)
            self._scroll.setVisible(False)
            return

        self._emptyLabel.setVisible(False)
        self._scroll.setVisible(True)

        for idx, (peer, fileInfo, isLocal, sharedAt) in enumerate(allFiles):
            row = FileRow(
                peerNickname=peer["nickname"],
                fileInfo=fileInfo,
                sharedAt=sharedAt,
                downloadManager=self._downloadManager,
                onDownload=self._onDownload,
                onCancel=self._onCancel,
                onRemoveShare=self._onRemoveShare,
                rowRegistry=self._fileRows,
                isLocal=isLocal,
            )
            self._layout.insertWidget(idx, row)

    def updateProgress(self, fileId, receivedBytes):
        row = self._fileRows.get(fileId)
        if row:
            d = self._downloadManager.getDownload(fileId)
            if not d:
                return
            if d.get("status") != "downloading":
                return
            total = d["total_bytes"]
            row.setProgress(receivedBytes, total)