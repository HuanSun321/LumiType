from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF
from src.constants import COLOR_PINK_LIGHT, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR


class ProgressRing(QWidget):
    """Cute circular progress indicator."""

    def __init__(self):
        super().__init__()
        self._progress = 1.0

    def set_progress(self, progress: float):
        self._progress = max(0.0, min(1.0, progress))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height()) - 6
        rect = QRectF(3, 3, size, size)

        # Background ring — dashed for hand-drawn feel
        pen = QPen(QColor(COLOR_PINK_LIGHT), 4, Qt.PenStyle.DashLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Progress ring
        if self._progress > 0:
            if self._progress > 0.2:
                color = QColor(COLOR_SUCCESS)
            elif self._progress > 0.1:
                color = QColor(COLOR_WARNING)
            else:
                color = QColor(COLOR_ERROR)

            pen = QPen(color, 5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            span = int(self._progress * 360 * 16)
            start_angle = 90 * 16
            painter.drawArc(rect, start_angle, -span)
