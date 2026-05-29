from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog, QSizePolicy

class CenterPanel(QWidget):
    def __init__(self, sharedFiles, onFilesAdded, parent=None):
        super().__init__(parent)
        self._sharedFiles = sharedFiles
        self._onFilesAdded = onFilesAdded

        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._dropBox = QWidget()
        self._dropBox.setObjectName("dropBox")
        self._dropBox.setFixedSize(280, 200)
        self._dropBox.setCursor(Qt.CursorShape.PointingHandCursor)
        self._applyDefaultStyle()

        boxLayout = QVBoxLayout(self._dropBox)
        boxLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        boxLayout.setSpacing(8)

        self._iconLabel = QLabel("⌯⌲")
        self._iconLabel.setStyleSheet("font-size: 40px; color: #9E9E9E;")
        self._iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        boxLayout.addWidget(self._iconLabel)

        self._mainLabel = QLabel("Drag & Drop files here")
        self._mainLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mainLabel.setStyleSheet("font-size: 14px; font-weight: 500;")
        boxLayout.addWidget(self._mainLabel)

        self._subLabel = QLabel("or click to browse")
        self._subLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subLabel.setStyleSheet("font-size: 12px; color: #9E9E9E;")
        boxLayout.addWidget(self._subLabel)

        outer.addWidget(self._dropBox)
        self._dropBox.mousePressEvent = self._openBrowser

    def _applyDefaultStyle(self):
        self._dropBox.setStyleSheet("""
            QWidget#dropBox {
                border: 2px dashed #BDBDBD;
                border-radius: 10px;
                background-color: transparent;
            }
        """)

    def _applyHoverStyle(self):
        self._dropBox.setStyleSheet("""
            QWidget#dropBox {
                border: 2px solid #2196F3;
                border-radius: 10px;
                background-color: rgba(33, 150, 243, 0.05);
            }
        """)

    def _openBrowser(self, event):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select files to share")
        if paths:
            self._addPaths(paths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._applyHoverStyle()

    def dragLeaveEvent(self, event):
        self._applyDefaultStyle()

    def dropEvent(self, event):
        self._applyDefaultStyle()
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self._addPaths(paths)
        event.acceptProposedAction()

    def _addPaths(self, paths):
        added = 0
        for p in paths:
            result = self._sharedFiles.addFile(p)
            if result is not None:
                added += 1
        if added > 0:
            self._onFilesAdded()
            self._showConfirmation(added)

    def _showConfirmation(self, count):
        self._mainLabel.setText(f"✓ {count} file{'s' if count != 1 else ''} added")
        self._mainLabel.setStyleSheet("font-size: 14px; font-weight: 500; color: #4CAF50;")
        self._subLabel.setVisible(False)
        self._iconLabel.setVisible(False)
        QTimer.singleShot(2000, self._resetLabels)

    def _resetLabels(self):
        self._mainLabel.setText("Drag & Drop files here")
        self._mainLabel.setStyleSheet("font-size: 14px; font-weight: 500;")
        self._subLabel.setVisible(True)
        self._iconLabel.setVisible(True)