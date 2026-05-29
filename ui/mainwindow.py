import os
import json
from .toast import ToastManager
from PyQt6.QtCore import QEvent, Qt, QTimer
from .leftpanel import LeftPanel
from .rightpanel import RightPanel
from .centerpanel import CenterPanel
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QFrame, QFileDialog, QVBoxLayout, QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self, localIp, configPath, signals, sharedFiles, peerRegistry,
                 discoveryService, downloadManager, nicknameHolder=None):
        super().__init__()
        self._localIp = localIp
        self._configPath = configPath
        self._signals = signals
        self._sharedFiles = sharedFiles
        self._peerRegistry = peerRegistry
        self._discovery = discoveryService
        self._downloadManager = downloadManager
        self._nicknameHolder = nicknameHolder if nicknameHolder is not None else [None]
        self._nickname = self._loadNickname()

        self.setWindowTitle("Pigeon")
        self.setMinimumSize(900, 600)

        self._buildUi()
        QApplication.instance().installEventFilter(self)
        self._connectSignals()
        self._toastManager = ToastManager(self)
        self._timeRefreshTimer = QTimer(self)
        self._timeRefreshTimer.timeout.connect(self._refreshLeftPanel)
        self._timeRefreshTimer.start(30000)

    def _loadNickname(self):
        if os.path.exists(self._configPath):
            try:
                with open(self._configPath) as f:
                    return json.load(f).get("nickname", "User")
            except Exception:
                pass
        return "User"

    def _buildUi(self):
        central = QWidget()
        self.setCentralWidget(central)
        mainLayout = QVBoxLayout(central)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        topRow = QWidget()
        topLayout = QHBoxLayout(topRow)
        topLayout.setContentsMargins(0, 0, 0, 0)
        topLayout.setSpacing(0)

        self._leftPanel = LeftPanel(
            downloadManager=self._downloadManager,
            onDownload=self._onDownloadRequested,
            onCancel=self._onCancel,
            onRemoveShare=self._onRemoveShare,
        )
        topLayout.addWidget(self._leftPanel)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFrameShadow(QFrame.Shadow.Sunken)
        topLayout.addWidget(divider)

        self._centerPanel = CenterPanel(
            sharedFiles=self._sharedFiles,
            onFilesAdded=self._onSharedFilesChanged,
        )
        topLayout.addWidget(self._centerPanel)

        self._rightPanel = RightPanel(
            configPath=self._configPath,
            onNicknameChange=self._onNicknameChanged,
        )
        self._rightPanel.setNickname(self._nickname)
        topLayout.addWidget(self._rightPanel)

        mainLayout.addWidget(topRow, stretch=1)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._clearNicknameFocus)

    def _clearNicknameFocus(self):
        self._rightPanel._nicknameInput.clearFocus()
        self._centerPanel.setFocus(Qt.FocusReason.OtherFocusReason)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            nicknameInput = self._rightPanel._nicknameInput
            if QApplication.focusWidget() is nicknameInput:
                globalPos = event.globalPosition().toPoint()
                clicked = QApplication.widgetAt(globalPos)
                if clicked is not nicknameInput and (
                    clicked is None or not nicknameInput.isAncestorOf(clicked)
                ):
                    nicknameInput.clearFocus()
        return super().eventFilter(watched, event)

    def _connectSignals(self):
        self._signals.peerUpdated.connect(self._onPeerUpdated)
        self._signals.peerOffline.connect(self._onPeerOffline)
        self._signals.peerJoined.connect(self._onPeerJoined)
        self._signals.downloadProgress.connect(self._onDownloadProgress)
        self._signals.downloadComplete.connect(self._onDownloadComplete)
        self._signals.downloadError.connect(self._onDownloadError)

    def _refreshLeftPanel(self):
        peers = self._peerRegistry.getAll()
        localFiles = self._sharedFiles.getAll()
        self._leftPanel.refresh(peers, self._localIp, localFiles, self._nickname)

    def _onPeerUpdated(self, peers):
        self._refreshLeftPanel()

    def _onPeerOffline(self, ip):
        self._refreshLeftPanel()

    def _onPeerJoined(self, nickname, fileCount):
        self._toastManager.show(f"● {nickname} joined", f"Sharing {fileCount} file{'s' if fileCount != 1 else ''}")

    def _onDownloadProgress(self, fileId, receivedBytes):
        self._leftPanel.updateProgress(fileId, receivedBytes)

    def _onDownloadComplete(self, fileId):
        d = self._downloadManager.getDownload(fileId)
        if d:
            self._toastManager.show("✓ Download complete", d["filename"])
        self._refreshLeftPanel()

    def _onDownloadError(self, fileId, message):
        self._refreshLeftPanel()

    def _onSharedFilesChanged(self):
        self._refreshLeftPanel()

    def _onNicknameChanged(self, nickname):
        self._nickname = nickname
        self._nicknameHolder[0] = nickname
        self._refreshLeftPanel()

    def _onDownloadRequested(self, fileInfo, resume=False):
        fileId = fileInfo["file_id"]
        peerIp = None
        peerNickname = ""
        tcpPort = 50002

        peers = self._peerRegistry.getAll()
        for p in peers.values():
            for f in p.get("files", []):
                if f["file_id"] == fileId:
                    peerIp = p["ip"]
                    peerNickname = p.get("nickname", p["ip"])
                    tcpPort = p.get("tcp_port", 50002)
                    break

        if not peerIp:
            return

        destinationPath = None
        if not resume:
            destinationPath, _ = QFileDialog.getSaveFileName(
                self,
                "Save File As",
                fileInfo["filename"],
                "All Files (*)",
            )
            if not destinationPath:
                return

        self._downloadManager.startDownload(
            fileId=fileId,
            peerIp=peerIp,
            tcpPort=tcpPort,
            filename=fileInfo["filename"],
            totalBytes=fileInfo["size_bytes"],
            peerNickname=peerNickname,
            destinationPath=destinationPath,
        )
        self._refreshLeftPanel()

    def _onCancel(self, fileId):
        self._downloadManager.cancelDownload(fileId)
        self._refreshLeftPanel()

    def _onRemoveShare(self, fileId):
        self._sharedFiles.removeFile(fileId)
        self._refreshLeftPanel()

    def closeEvent(self, event):
        self._discovery.stop()
        super().closeEvent(event)