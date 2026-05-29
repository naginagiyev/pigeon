import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QFrame

class RightPanel(QWidget):
    def __init__(self, configPath, onNicknameChange, parent=None):
        super().__init__(parent)
        self._configPath = configPath
        self._onNicknameChange = onNicknameChange
        self._savedNickname = ""

        self.setFixedWidth(220)
        self.setObjectName("rightPanel")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(12)

        nicknameBox = QFrame()
        nicknameBox.setObjectName("nicknameBox")
        nicknameBox.setStyleSheet("""
            QFrame#nicknameBox {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        nbLayout = QVBoxLayout(nicknameBox)
        nbLayout.setContentsMargins(8, 8, 8, 8)
        nbLayout.setSpacing(4)

        nnTitle = QLabel("Herald 📯")
        nnTitle.setStyleSheet("color: #9E9E9E; font-size: 11px;")
        nbLayout.addWidget(nnTitle)

        self._nicknameInput = QLineEdit()
        self._nicknameInput.setMaxLength(20)
        self._nicknameInput.setPlaceholderText("Enter nickname")
        self._nicknameInput.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._nicknameInput.textChanged.connect(self._onNicknameTextChanged)
        self._nicknameInput.editingFinished.connect(self._onNicknameEditingFinished)
        nbLayout.addWidget(self._nicknameInput)

        outer.addWidget(nicknameBox)
        outer.addStretch()

    def setNickname(self, nickname):
        self._savedNickname = nickname
        self._nicknameInput.blockSignals(True)
        self._nicknameInput.setText(nickname)
        self._nicknameInput.blockSignals(False)
        self._nicknameInput.clearFocus()

    def _onNicknameTextChanged(self, text):
        if " " in text or len(text) == 0:
            self._nicknameInput.setStyleSheet("border: 1px solid #F44336;")
        else:
            self._nicknameInput.setStyleSheet("")

    def _onNicknameEditingFinished(self):
        text = self._nicknameInput.text().strip()
        if not text or " " in text or text == self._savedNickname:
            return
        self._savedNickname = text
        self._saveNickname(text)
        self._onNicknameChange(text)

    def _saveNickname(self, nickname):
        config = {}
        if os.path.exists(self._configPath):
            try:
                with open(self._configPath, "r") as f:
                    config = json.load(f)
            except Exception:
                pass
        config["nickname"] = nickname
        try:
            with open(self._configPath, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass