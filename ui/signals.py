from PyQt6.QtCore import QObject, pyqtSignal

class AppSignals(QObject):
    peerUpdated = pyqtSignal(dict)
    peerOffline = pyqtSignal(str)
    peerJoined = pyqtSignal(str, int)
    downloadProgress = pyqtSignal(str, int)
    downloadComplete = pyqtSignal(str)
    downloadError = pyqtSignal(str, str)