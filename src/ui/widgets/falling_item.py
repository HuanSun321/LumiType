import math
import random
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QBrush, QPainterPath
from src.app import App
from src.constants import DEFAULT_FONT_SIZE


# Falling frame shape types.
DECO_TYPES = ["star", "heart", "flower", "bubble", "cloud", "butterfly", "rainbow", "crown"]
DECO_LABELS = {
    "random": "随机外框",
    "star": "星星外框",
    "heart": "爱心外框",
    "flower": "花瓣外框",
    "bubble": "气泡外框",
    "cloud": "云朵外框",
    "butterfly": "蝴蝶外框",
    "rainbow": "彩虹外框",
    "crown": "皇冠外框",
}

FRAME_PAD_X = 24
FRAME_PAD_TOP = 14
FRAME_PAD_BOTTOM = 16
PINYIN_LINE_HEIGHT = 24


class FallingCharItem(QGraphicsObject):
    """A single Chinese character that falls with a shaped frame and pinyin hint."""

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
        pinyin_h = PINYIN_LINE_HEIGHT if pinyin else 0
        content_w = max(self._char_width, pinyin_w) + FRAME_PAD_X * 2
        content_h = FRAME_PAD_TOP + self._char_height + pinyin_h + FRAME_PAD_BOTTOM
        frame_size = max(content_w, content_h)
        self._item_width = frame_size
        self._item_height = frame_size

        # Pick frame shape from config.
        config = App.instance().config
        deco_setting = config.get("falling_deco") or "random"
        if deco_setting == "random":
            self._frame_type = random.choice(DECO_TYPES)
        else:
            self._frame_type = deco_setting if deco_setting in DECO_TYPES else "bubble"

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
        pad = 8
        return QRectF(-pad, -pad, self._item_width + pad * 2, self._item_height + pad * 2)

    def _frame_rect(self) -> QRectF:
        return QRectF(0, 0, self._item_width, self._item_height).adjusted(1, 1, -1, -1)

    def _content_top(self) -> float:
        pinyin_h = PINYIN_LINE_HEIGHT if self._pinyin else 0
        content_h = self._char_height + pinyin_h
        return (self._item_height - content_h) / 2

    def _char_text_rect(self) -> QRectF:
        return QRectF(0, self._content_top() - 2, self._item_width, self._char_height + 4)

    def _pinyin_text_rect(self) -> QRectF:
        return QRectF(0, self._content_top() + self._char_height, self._item_width, PINYIN_LINE_HEIGHT)

    def _text_bounds(self) -> QRectF:
        char_rect = self._char_text_rect()
        char_bounds = QRectF(
            (self._item_width - self._char_width) / 2,
            char_rect.y(),
            self._char_width,
            char_rect.height(),
        )
        if not self._pinyin:
            return char_bounds

        pinyin_w = self._pinyin_fm.horizontalAdvance(self._pinyin)
        pinyin_rect = self._pinyin_text_rect()
        pinyin_bounds = QRectF(
            (self._item_width - pinyin_w) / 2,
            pinyin_rect.y(),
            pinyin_w,
            pinyin_rect.height(),
        )
        return char_bounds.united(pinyin_bounds)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._opacity <= 0:
            return

        painter.setOpacity(self._opacity)

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

        frame_path = self._frame_path(self._frame_rect())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawPath(frame_path)
        painter.setPen(QPen(border_color, 2, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(frame_path)

        # Character text
        char_color = QColor("#5B4A4A")
        painter.setPen(char_color)
        painter.setFont(self._font)
        painter.drawText(
            self._char_text_rect(),
            Qt.AlignmentFlag.AlignCenter,
            self._char,
        )

        # Pinyin hint below the character (increased height for descenders)
        if self._pinyin:
            painter.setFont(self._pinyin_font)
            painter.setPen(QColor("#A08888"))
            painter.drawText(
                self._pinyin_text_rect(),
                Qt.AlignmentFlag.AlignCenter,
                self._pinyin,
            )

    def _frame_path(self, rect: QRectF) -> QPainterPath:
        """Return the whole outer frame shape."""
        frame_type = self._frame_type
        if frame_type == "heart":
            return self._heart_frame_path(rect)
        if frame_type == "star":
            return self._star_frame_path(rect)
        if frame_type == "flower":
            return self._flower_frame_path(rect)
        if frame_type == "cloud":
            return self._cloud_frame_path(rect)
        if frame_type == "butterfly":
            return self._butterfly_frame_path(rect)
        if frame_type == "rainbow":
            return self._rainbow_frame_path(rect)
        if frame_type == "crown":
            return self._crown_frame_path(rect)
        if frame_type == "bubble":
            return self._bubble_frame_path(rect)

        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)
        return path

    def _heart_frame_path(self, rect: QRectF) -> QPainterPath:
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        path = QPainterPath()
        path.moveTo(x + w * 0.50, y + h * 0.92)
        path.cubicTo(x + w * 0.24, y + h * 0.76, x + w * 0.07, y + h * 0.60, x + w * 0.07, y + h * 0.37)
        path.cubicTo(x + w * 0.07, y + h * 0.13, x + w * 0.32, y + h * 0.05, x + w * 0.50, y + h * 0.27)
        path.cubicTo(x + w * 0.68, y + h * 0.05, x + w * 0.93, y + h * 0.13, x + w * 0.93, y + h * 0.37)
        path.cubicTo(x + w * 0.93, y + h * 0.60, x + w * 0.76, y + h * 0.76, x + w * 0.50, y + h * 0.92)
        path.closeSubpath()
        return path

    def _star_frame_path(self, rect: QRectF) -> QPainterPath:
        cx, cy = rect.center().x(), rect.center().y()
        outer = rect.width() * 0.48
        inner = outer * 0.72
        points = []
        for i in range(10):
            radius = outer if i % 2 == 0 else inner
            angle = math.radians(-90 + i * 36)
            points.append(QPointF(cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
        return self._rounded_polygon_path(points, radius=0.34)

    def _rounded_polygon_path(self, points: list[QPointF], radius: float = 0.30) -> QPainterPath:
        path = QPainterPath()
        if not points:
            return path
        starts = []
        ends = []
        for i, point in enumerate(points):
            prev_point = points[i - 1]
            next_point = points[(i + 1) % len(points)]
            starts.append(QPointF(
                point.x() + (prev_point.x() - point.x()) * radius,
                point.y() + (prev_point.y() - point.y()) * radius,
            ))
            ends.append(QPointF(
                point.x() + (next_point.x() - point.x()) * radius,
                point.y() + (next_point.y() - point.y()) * radius,
            ))
        path.moveTo(ends[0])
        for i, point in enumerate(points[1:], start=1):
            path.lineTo(starts[i])
            path.quadTo(point, ends[i])
        path.lineTo(starts[0])
        path.quadTo(points[0], ends[0])
        path.closeSubpath()
        return path

    def _flower_frame_path(self, rect: QRectF) -> QPainterPath:
        cx, cy = rect.center().x(), rect.center().y()
        radius = rect.width() * 0.42
        path = QPainterPath()
        for i in range(96):
            angle = (math.pi * 2 * i) / 96
            wave = 1 + 0.12 * math.cos(angle * 8)
            point = QPointF(cx + math.cos(angle) * radius * wave, cy + math.sin(angle) * radius * wave)
            if i == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        path.closeSubpath()
        return path

    def _cloud_frame_path(self, rect: QRectF) -> QPainterPath:
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        path = QPainterPath()
        path.moveTo(x + w * 0.16, y + h * 0.76)
        path.cubicTo(x + w * 0.02, y + h * 0.72, x + w * 0.03, y + h * 0.45, x + w * 0.20, y + h * 0.43)
        path.cubicTo(x + w * 0.16, y + h * 0.25, x + w * 0.34, y + h * 0.14, x + w * 0.47, y + h * 0.25)
        path.cubicTo(x + w * 0.50, y + h * 0.08, x + w * 0.74, y + h * 0.10, x + w * 0.78, y + h * 0.32)
        path.cubicTo(x + w * 0.96, y + h * 0.34, x + w * 1.00, y + h * 0.62, x + w * 0.84, y + h * 0.74)
        path.cubicTo(x + w * 0.70, y + h * 0.90, x + w * 0.30, y + h * 0.90, x + w * 0.16, y + h * 0.76)
        path.closeSubpath()
        return path

    def _bubble_frame_path(self, rect: QRectF) -> QPainterPath:
        path = QPainterPath()
        path.addEllipse(rect.adjusted(rect.width() * 0.04, rect.height() * 0.04, -rect.width() * 0.04, -rect.height() * 0.04))
        return path

    def _butterfly_frame_path(self, rect: QRectF) -> QPainterPath:
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        path = QPainterPath()
        path.moveTo(x + w * 0.50, y + h * 0.22)
        path.cubicTo(x + w * 0.28, y + h * 0.02, x + w * 0.04, y + h * 0.14, x + w * 0.16, y + h * 0.45)
        path.cubicTo(x + w * 0.01, y + h * 0.74, x + w * 0.24, y + h * 1.00, x + w * 0.50, y + h * 0.74)
        path.cubicTo(x + w * 0.76, y + h * 1.00, x + w * 0.99, y + h * 0.74, x + w * 0.84, y + h * 0.45)
        path.cubicTo(x + w * 0.96, y + h * 0.14, x + w * 0.72, y + h * 0.02, x + w * 0.50, y + h * 0.22)
        path.closeSubpath()
        return path

    def _rainbow_frame_path(self, rect: QRectF) -> QPainterPath:
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        path = QPainterPath()
        path.moveTo(x + w * 0.11, y + h * 0.91)
        path.lineTo(x + w * 0.11, y + h * 0.50)
        path.cubicTo(x + w * 0.11, y + h * 0.14, x + w * 0.32, y + h * 0.07, x + w * 0.50, y + h * 0.07)
        path.cubicTo(x + w * 0.68, y + h * 0.07, x + w * 0.89, y + h * 0.14, x + w * 0.89, y + h * 0.50)
        path.lineTo(x + w * 0.89, y + h * 0.91)
        path.cubicTo(x + w * 0.72, y + h * 0.99, x + w * 0.28, y + h * 0.99, x + w * 0.11, y + h * 0.91)
        path.closeSubpath()
        return path

    def _crown_frame_path(self, rect: QRectF) -> QPainterPath:
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        points = [
            QPointF(x + w * 0.12, y + h * 0.91),
            QPointF(x + w * 0.12, y + h * 0.35),
            QPointF(x + w * 0.31, y + h * 0.50),
            QPointF(x + w * 0.50, y + h * 0.05),
            QPointF(x + w * 0.69, y + h * 0.50),
            QPointF(x + w * 0.88, y + h * 0.35),
            QPointF(x + w * 0.88, y + h * 0.91),
        ]
        return self._rounded_polygon_path(points, radius=0.15)
