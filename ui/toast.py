from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import QPropertyAnimation, QTimer, QEasingCurve, Qt

class ToastNotification(QFrame):
    def __init__(self, line1, line2, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("toast")
        self.setStyleSheet("""
            QFrame#toast {
                background-color: #323232;
                border-radius: 6px;
                padding: 4px;
            }
            QLabel { color: #ffffff; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        l1 = QLabel(line1)
        l1.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(l1)

        if line2:
            l2 = QLabel(line2)
            l2.setStyleSheet("font-size: 12px; color: #cccccc;")
            layout.addWidget(l2)

        self.adjustSize()

        QTimer.singleShot(4000, self._startFade)

    def _startFade(self):
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(self.deleteLater)
        self._anim.start()

class ToastManager:
    def __init__(self, parentWindow):
        self._parent = parentWindow
        self._toasts = []

    def show(self, line1, line2=""):
        toast = ToastNotification(line1, line2, self._parent)
        toast.show()
        self._toasts.append(toast)
        toast.destroyed.connect(lambda: self._remove(toast))
        self._reposition()

    def _remove(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition()

    def _reposition(self):
        parentRect = self._parent.rect()
        margin = 12
        spacing = 8
        y = parentRect.bottom() - margin
        for toast in reversed(self._toasts):
            if not toast.isVisible():
                continue
            toast.adjustSize()
            x = parentRect.right() - toast.width() - margin
            y -= toast.height()
            pos = self._parent.mapToGlobal(self._parent.rect().topLeft())
            toast.move(pos.x() + x, pos.y() + y)
            y -= spacing