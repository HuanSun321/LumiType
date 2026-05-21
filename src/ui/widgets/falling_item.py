import math
import random
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush, QPainterPath
from src.app import App
from src.constants import COLOR_PINK_LIGHT, DEFAULT_FONT_SIZE


# Decorative pattern types
DECO_TYPES = ["star", "heart", "flower", "bubble", "cloud", "butterfly", "rainbow", "crown"]
DECO_LABELS = {
    "random": "随机",
    "star": "星星",
    "heart": "爱心",
    "flower": "花朵",
    "bubble": "气泡",
    "cloud": "云朵",
    "butterfly": "蝴蝶",
    "rainbow": "彩虹",
    "crown": "皇冠",
}


class FallingCharItem(QGraphicsObject):
    """A single Chinese character that falls — cute bubble style with pinyin hint and decorations."""

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

        self._pinyin_font = QFont(font.family(), max(font.pointSize() - 8, 9))
        self._pinyin_fm = QFontMetrics(self._pinyin_font)

        pinyin_w = self._pinyin_fm.horizontalAdvance(pinyin) if pinyin else 0
        self._item_width = max(self._char_width, pinyin_w) + 32
        self._item_height = self._char_height + 38 if pinyin else self._char_height + 20

        # Pick decoration type from config
        config = App.instance().config
        deco_setting = config.get("falling_deco") or "random"
        if deco_setting == "random":
            self._deco_type = random.choice(DECO_TYPES)
        else:
            self._deco_type = deco_setting if deco_setting in DECO_TYPES else "star"

        # Pre-compute decoration positions and rotations (fixed per item)
        self._deco_positions = self._compute_deco_positions()
        self._deco_rotations = [random.uniform(-15, 15) for _ in self._deco_positions]

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
                # Don't emit signal here — on_tick() handles cleanup
                return False
        else:
            self.moveBy(0, self._speed * dt_seconds)
        self.update()
        return True

    def boundingRect(self) -> QRectF:
        # Extra padding for decoration rotation overshoot
        pad = 8
        return QRectF(-pad, -pad, self._item_width + pad * 2, self._item_height + pad * 2)

    def _compute_deco_positions(self) -> list[tuple[float, float]]:
        """Return (x, y) positions for small decorations around the bubble corners."""
        m = 4  # margin from edge
        s = 5  # offset inward
        w, h = self._item_width, self._item_height
        return [
            (m + s, m + s),         # top-left
            (w - m - s, m + s),     # top-right
            (m + s, h - m - s),     # bottom-left
            (w - m - s, h - m - s), # bottom-right
        ]

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

        # Draw decorative patterns around the bubble
        self._draw_decorations(painter)

        # Character text
        char_color = QColor("#5B4A4A")
        painter.setPen(char_color)
        painter.setFont(self._font)
        painter.drawText(
            QRectF(0, 2, self._item_width, self._char_height + 6),
            Qt.AlignmentFlag.AlignCenter,
            self._char,
        )

        # Pinyin hint below the character (increased height for descenders)
        if self._pinyin:
            painter.setFont(self._pinyin_font)
            painter.setPen(QColor("#A08888"))
            painter.drawText(
                QRectF(0, self._char_height + 6, self._item_width, 28),
                Qt.AlignmentFlag.AlignCenter,
                self._pinyin,
            )

    def _draw_decorations(self, painter: QPainter):
        """Draw small hand-drawn style decorations at bubble corners."""
        deco_color = QColor(255, 143, 171, 80)  # pink, semi-transparent
        painter.save()

        for i, (dx, dy) in enumerate(self._deco_positions):
            painter.save()
            painter.translate(dx, dy)
            painter.rotate(self._deco_rotations[i])

            if self._deco_type == "star":
                self._paint_star(painter, deco_color)
            elif self._deco_type == "heart":
                self._paint_heart(painter, deco_color)
            elif self._deco_type == "flower":
                self._paint_flower(painter, i)
            elif self._deco_type == "bubble":
                self._paint_bubble(painter)
            elif self._deco_type == "cloud":
                self._paint_cloud(painter)
            elif self._deco_type == "butterfly":
                self._paint_butterfly(painter, deco_color)
            elif self._deco_type == "rainbow":
                self._paint_rainbow(painter)
            elif self._deco_type == "crown":
                self._paint_crown(painter, deco_color)

            painter.restore()

        painter.restore()

    def _paint_star(self, painter: QPainter, color: QColor):
        """Draw a small 5-pointed star."""
        size = 5
        path = QPainterPath()
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            outer = QPointF(math.cos(angle) * size, math.sin(angle) * size)
            inner_angle = math.radians(i * 72 + 36 - 90)
            inner = QPointF(math.cos(inner_angle) * size * 0.4, math.sin(inner_angle) * size * 0.4)
            if i == 0:
                path.moveTo(outer)
            else:
                path.lineTo(outer)
            path.lineTo(inner)
        path.closeSubpath()
        painter.setPen(QPen(QColor(255, 215, 0, 120), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(255, 215, 0, 60)))
        painter.drawPath(path)

    def _paint_heart(self, painter: QPainter, color: QColor):
        """Draw a small heart using bezier curves."""
        size = 5
        path = QPainterPath()
        path.moveTo(0, size * 0.3)
        path.cubicTo(-size, -size * 0.5, -size * 0.5, -size, 0, -size * 0.3)
        path.cubicTo(size * 0.5, -size, size, -size * 0.5, 0, size * 0.3)
        painter.setPen(QPen(QColor(255, 143, 171, 100), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(255, 143, 171, 50)))
        painter.drawPath(path)

    def _paint_flower(self, painter: QPainter, index: int):
        """Draw a small flower with petals."""
        petal_colors = [
            QColor(255, 209, 220, 80),  # pink
            QColor(232, 218, 239, 80),  # lavender
            QColor(213, 245, 227, 80),  # mint
            QColor(253, 235, 208, 80),  # peach
        ]
        color = petal_colors[index % len(petal_colors)]
        painter.setPen(QPen(color.darker(120), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(color))
        for i in range(5):
            angle = math.radians(i * 72)
            px = math.cos(angle) * 4
            py = math.sin(angle) * 4
            painter.drawEllipse(QPointF(px, py), 3, 2)
        painter.setBrush(QBrush(QColor(255, 255, 150, 100)))
        painter.drawEllipse(QPointF(0, 0), 2, 2)

    def _paint_bubble(self, painter: QPainter):
        """Draw small circles."""
        painter.setPen(QPen(QColor(174, 214, 241, 100), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(214, 234, 248, 50)))
        for i in range(3):
            r = 2 + i
            painter.drawEllipse(QPointF(i * 3 - 3, -i * 2), r, r)

    def _paint_cloud(self, painter: QPainter):
        """Draw a small cloud from overlapping ellipses."""
        painter.setPen(QPen(QColor(200, 200, 200, 80), 1, Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
        painter.drawEllipse(QPointF(-3, 0), 4, 3)
        painter.drawEllipse(QPointF(2, -1), 3, 2.5)
        painter.drawEllipse(QPointF(0, -2), 3.5, 2)

    def _paint_butterfly(self, painter: QPainter, color: QColor):
        """Draw a small butterfly."""
        painter.setPen(QPen(QColor(200, 180, 220, 100), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(232, 218, 239, 60)))
        # Wings
        painter.drawEllipse(QPointF(-3, 0), 4, 3)
        painter.drawEllipse(QPointF(3, 0), 4, 3)
        # Body
        painter.setPen(QPen(QColor(150, 130, 170, 100), 1.5))
        painter.drawLine(QPointF(0, -3), QPointF(0, 3))

    def _paint_rainbow(self, painter: QPainter):
        """Draw small rainbow arcs."""
        colors = [QColor(255, 143, 171, 60), QColor(255, 215, 0, 60), QColor(174, 214, 241, 60)]
        for i, c in enumerate(colors):
            pen = QPen(c, 1.5, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = 6 + i * 2
            painter.drawArc(QRectF(-r, -r, r * 2, r * 2), 0, 180 * 16)

    def _paint_crown(self, painter: QPainter, color: QColor):
        """Draw a small crown."""
        path = QPainterPath()
        s = 5
        path.moveTo(-s, s * 0.3)
        path.lineTo(-s, -s * 0.3)
        path.lineTo(-s * 0.5, 0)
        path.lineTo(0, -s * 0.5)
        path.lineTo(s * 0.5, 0)
        path.lineTo(s, -s * 0.3)
        path.lineTo(s, s * 0.3)
        path.closeSubpath()
        painter.setPen(QPen(QColor(255, 200, 100, 100), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(255, 215, 0, 50)))
        painter.drawPath(path)
