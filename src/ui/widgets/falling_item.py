from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush
from src.app import App
from src.constants import COLOR_PINK_LIGHT, DEFAULT_FONT_SIZE


class FallingCharItem(QGraphicsObject):
    """A single Chinese character that falls — cute bubble style with pinyin hint."""

    eliminated = pyqtSignal()

    STATE_FALLING = 0
    STATE_TARGETED = 1
    STATE_ELIMINATED = 2

    def __init__(self, char: str, x: float, y: float, speed: float,
                 font: QFont = None, pinyin: str = ""):
        super().__init__()
        if font is None:
            config = App.instance().config
            font_family = config.get("font_family") or "Microsoft YaHei"
            font_size = config.get("font_size") or DEFAULT_FONT_SIZE
            font = QFont(font_family, font_size)
        super().__init__()
        self._char = char
        self._speed = speed
        self._state = self.STATE_FALLING
        self._opacity = 1.0
        self._eliminate_timer = 0.0
        self._pinyin = pinyin

        fm = QFontMetrics(font)
        self._char_width = fm.horizontalAdvance(char)
        self._char_height = fm.height()
        self._font = font

        # Pinyin font (smaller)
        self._pinyin_font = QFont(font.family(), max(font.pointSize() - 8, 9))
        self._pinyin_fm = QFontMetrics(self._pinyin_font)

        # Width: take the wider of character or pinyin + padding
        pinyin_w = self._pinyin_fm.horizontalAdvance(pinyin) if pinyin else 0
        self._item_width = max(self._char_width, pinyin_w) + 28
        self._item_height = self._char_height + 30 if pinyin else self._char_height + 18

        self.setPos(x, y)

    @property
    def char(self) -> str:
        return self._char

    @property
    def state(self) -> int:
        return self._state

    @property
    def speed(self) -> float:
        return self._speed

    def set_speed(self, speed: float):
        self._speed = speed

    def set_targeted(self):
        self._state = self.STATE_TARGETED
        self.update()

    def set_falling(self):
        self._state = self.STATE_FALLING
        self.update()

    def eliminate(self):
        self._state = self.STATE_ELIMINATED
        self._eliminate_timer = 0.3
        self.update()

    def advance(self, dt_seconds: float):
        if self._state == self.STATE_ELIMINATED:
            self._eliminate_timer -= dt_seconds
            self._opacity = max(0.0, self._eliminate_timer / 0.3)
            if self._eliminate_timer <= 0:
                self.eliminated.emit()
                return False
        else:
            self.moveBy(0, self._speed * dt_seconds)
        self.update()
        return True

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._item_width, self._item_height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._opacity <= 0:
            return

        painter.setOpacity(self._opacity)

        rect = self.boundingRect()

        # Cute bubble background
        bg_colors = {
            self.STATE_FALLING: QColor("#D6EAF8"),
            self.STATE_TARGETED: QColor("#FFD1DC"),
            self.STATE_ELIMINATED: QColor("#D5F5E3"),
        }
        border_colors = {
            self.STATE_FALLING: QColor("#AED6F1"),
            self.STATE_TARGETED: QColor("#FF8FAB"),
            self.STATE_ELIMINATED: QColor("#8BD3A8"),
        }

        bg_color = bg_colors.get(self._state, QColor("#D6EAF8"))
        border_color = border_colors.get(self._state, QColor("#AED6F1"))

        # Dashed border for hand-drawn feel
        pen = QPen(border_color, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 12, 12)

        # Character text
        char_color = QColor("#5B4A4A")
        painter.setPen(char_color)
        painter.setFont(self._font)
        painter.drawText(
            QRectF(0, 0, self._item_width, self._char_height + 4),
            Qt.AlignmentFlag.AlignCenter,
            self._char,
        )

        # Pinyin hint below the character
        if self._pinyin:
            painter.setFont(self._pinyin_font)
            painter.setPen(QColor("#A08888"))
            painter.drawText(
                QRectF(0, self._char_height + 2, self._item_width, 20),
                Qt.AlignmentFlag.AlignCenter,
                self._pinyin,
            )
