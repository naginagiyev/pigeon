import os
import sys
import json
import random
import socket
from ui.signals import AppSignals
from core.server import FileServer
from ui.mainwindow import MainWindow
from core.registry import PeerRegistry
from core.sharedfiles import SharedFiles
from core.downloader import DownloadManager
from core.discovery import DiscoveryService
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtWidgets import QApplication, QMessageBox

def bundleDir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def appDir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def resourcePath(*parts):
    return os.path.join(bundleDir(), *parts)

def getAppDataDir():
    appDataRoot = os.environ.get("APPDATA")
    if not appDataRoot:
        appDataRoot = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    pigeonDir = os.path.join(appDataRoot, "Pigeon")
    os.makedirs(pigeonDir, exist_ok=True)
    return pigeonDir

CONFIG_PATH = os.path.join(getAppDataDir(), "lanshare.config.json")
LEGACY_CONFIG_PATH = os.path.join(appDir(), "lanshare.config.json")

def buildAppIcon():
    return QIcon(resourcePath("assets", "logo.ico"))

def applyDarkPalette(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 20))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 99, 71))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(130, 130, 130))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(130, 130, 130))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(130, 130, 130))
    app.setPalette(palette)

def applyWindowsDarkTitleBar(window):
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(window.winId())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd),
            ctypes.c_uint(20),
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        try:
            import ctypes
            hwnd = int(window.winId())
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd),
                ctypes.c_uint(19),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            pass

def getLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def generateRandomNickname():
    return f"Pigeon{random.randint(1000, 9999)}"

def loadConfig():
    if not os.path.exists(CONFIG_PATH) and os.path.exists(LEGACY_CONFIG_PATH):
        try:
            with open(LEGACY_CONFIG_PATH) as f:
                legacyConfig = json.load(f)
            saveConfig(legacyConfig)
        except Exception:
            pass
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def saveConfig(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    applyDarkPalette(app)
    appIcon = buildAppIcon()
    app.setWindowIcon(appIcon)

    config = loadConfig()
    if not config.get("nickname"):
        config["nickname"] = generateRandomNickname()
        saveConfig(config)

    localIp = getLocalIp()
    signals = AppSignals()

    sharedFiles = SharedFiles()
    peerRegistry = PeerRegistry(signals)

    nicknameHolder = [config["nickname"]]

    def getNickname():
        return nicknameHolder[0]

    discovery = DiscoveryService(
        localIp=localIp,
        nicknameGetter=getNickname,
        sharedFiles=sharedFiles,
        peerRegistry=peerRegistry,
    )

    try:
        fileServer = FileServer(sharedFiles)
        fileServer.start()
    except RuntimeError as e:
        QMessageBox.critical(None, "Port Error", str(e))
        sys.exit(1)

    downloadManager = DownloadManager(signals)
    peerRegistry.startTimeoutChecker()
    discovery.start()

    window = MainWindow(
        localIp=localIp,
        configPath=CONFIG_PATH,
        signals=signals,
        sharedFiles=sharedFiles,
        peerRegistry=peerRegistry,
        discoveryService=discovery,
        downloadManager=downloadManager,
        nicknameHolder=nicknameHolder,
    )
    window.setWindowIcon(appIcon)

    window.showMaximized()
    applyWindowsDarkTitleBar(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()