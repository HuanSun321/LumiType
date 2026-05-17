import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath


# Simplified QWERTY keyboard layout: list of (key_label, row, col, width_units)
_KEYBOARD_LAYOUT = [
    # Row 0: number row
    ("1", 0, 0, 1), ("2", 0, 1, 1), ("3", 0, 2, 1), ("4", 0, 3, 1), ("5", 0, 4, 1),
    ("6", 0, 5, 1), ("7", 0, 6, 1), ("8", 0, 7, 1), ("9", 0, 8, 1), ("0", 0, 9, 1),
    # Row 1: QWERTY
    ("Q", 1, 0, 1), ("W", 1, 1, 1), ("E", 1, 2, 1), ("R", 1, 3, 1), ("T", 1, 4, 1),
    ("Y", 1, 5, 1), ("U", 1, 6, 1), ("I", 1, 7, 1), ("O", 1, 8, 1), ("P", 1, 9, 1),
    # Row 2: ASDF
    ("A", 2, 0.5, 1), ("S", 2, 1.5, 1), ("D", 2, 2.5, 1), ("F", 2, 3.5, 1), ("G", 2, 4.5, 1),
    ("H", 2, 5.5, 1), ("J", 2, 6.5, 1), ("K", 2, 7.5, 1), ("L", 2, 8.5, 1),
    # Row 3: ZXCV
    ("Z", 3, 1, 1), ("X", 3, 2, 1), ("C", 3, 3, 1), ("V", 3, 4, 1), ("B", 3, 5, 1),
    ("N", 3, 6, 1), ("M", 3, 7, 1),
    # Row 4: Space
    ("SPACE", 4, 2, 5),
]

# Build key position map: key_name -> (row, col_center, width)
_KEY_MAP = {}
for label, row, col, w in _KEYBOARD_LAYOUT:
    _KEY_MAP[label.upper()] = (row, col + w / 2.0, w)


class KeyboardRabbitWidget(QWidget):
    """Hand-drawn cute rabbit pressing a keyboard. Bottom-right overlay during gameplay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Animation state
        self._pressed_keys: set[str] = set()
        self._arm_target: tuple[float, float] | None = None
        self._arm_current: tuple[float, float] = (0, 0)
        self._arm_rest: tuple[float, float] = (0, 0)
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start()

        # Keyboard geometry
        self._kb_x = 20
        self._kb_y = 130
        self._key_size = 22
        self._key_gap = 2
        self._key_unit = self._key_size + self._key_gap

        # Arm rest position (center of rabbit body, low)
        self._arm_rest = (160, 100)
        self._arm_current = (160.0, 100.0)

    def key_pressed(self, key_name: str):
        """Called when a key is pressed."""
        name = key_name.upper()
        if len(name) == 1 and name.isalpha():
            self._pressed_keys.add(name)
            pos = self._get_key_center(name)
            if pos:
                self._arm_target = pos
        elif name == " ":
            self._pressed_keys.add("SPACE")
            pos = self._get_key_center("SPACE")
            if pos:
                self._arm_target = pos
        self.update()

    def key_released(self, key_name: str):
        """Called when a key is released."""
        name = key_name.upper()
        self._pressed_keys.discard(name)
        self._pressed_keys.discard("SPACE")
        if not self._pressed_keys:
            self._arm_target = None
        self.update()

    def highlight_pinyin(self, pinyin: str):
        """Highlight keys matching the current composing pinyin string."""
        self._pressed_keys.clear()
        if pinyin:
            for ch in pinyin.upper():
                if ch.isalpha() or ch in _KEY_MAP:
                    self._pressed_keys.add(ch)
            # Move arm toward last key in the pinyin
            if pinyin:
                last_ch = pinyin[-1].upper()
                pos = self._get_key_center(last_ch)
                if pos:
                    self._arm_target = pos
        else:
            self._arm_target = None
        self.update()

    def clear_highlights(self):
        """Clear all key highlights."""
        self._pressed_keys.clear()
        self._arm_target = None
        self.update()

    def _get_key_center(self, key: str) -> tuple[float, float] | None:
        """Get the center (x, y) of a key on the keyboard."""
        info = _KEY_MAP.get(key.upper())
        if not info:
            return None
        row, col_center, w = info
        x = self._kb_x + col_center * self._key_unit
        y = self._kb_y + row * self._key_unit + self._key_size / 2
        return (x, y)

    def _animate(self):
        """Lerp arm position towards target."""
        target = self._arm_target if self._arm_target else self._arm_rest
        speed = 0.15
        cx, cy = self._arm_current
        tx, ty = target
        nx = cx + (tx - cx) * speed
        ny = cy + (ty - cy) * speed
        if abs(nx - cx) > 0.5 or abs(ny - cy) > 0.5:
            self._arm_current = (nx, ny)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Semi-transparent background
        painter.setOpacity(0.9)

        # Draw rabbit (upper part)
        self._draw_rabbit(painter)

        # Draw keyboard (lower part)
        self._draw_keyboard(painter)

        painter.end()

    def _draw_rabbit(self, painter: QPainter):
        """Draw a cute hand-drawn rabbit upper body."""
        cx, cy = 160, 65  # center of rabbit head

        # --- Ears ---
        ear_pen = QPen(QColor("#FF8FAB"), 1.5, Qt.PenStyle.DashLine)
        ear_fill = QBrush(QColor("#FFFFFF"))
        inner_fill = QBrush(QColor("#FFD1DC"))

        # Left ear
        painter.setPen(ear_pen)
        painter.setBrush(ear_fill)
        painter.drawEllipse(QPointF(cx - 15, cy - 38), 8, 22)
        painter.setBrush(inner_fill)
        painter.drawEllipse(QPointF(cx - 15, cy - 36), 5, 16)

        # Right ear
        painter.setPen(ear_pen)
        painter.setBrush(ear_fill)
        painter.drawEllipse(QPointF(cx + 15, cy - 38), 8, 22)
        painter.setBrush(inner_fill)
        painter.drawEllipse(QPointF(cx + 15, cy - 36), 5, 16)

        # --- Head ---
        head_pen = QPen(QColor("#FF8FAB"), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(head_pen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx, cy), 22, 20)

        # --- Eyes ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#5B4A4A")))
        painter.drawEllipse(QPointF(cx - 8, cy - 3), 3, 3)
        painter.drawEllipse(QPointF(cx + 8, cy - 3), 3, 3)

        # Eye highlights
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx - 7, cy - 4), 1.5, 1.5)
        painter.drawEllipse(QPointF(cx + 9, cy - 4), 1.5, 1.5)

        # --- Blush ---
        painter.setBrush(QBrush(QColor(255, 182, 193, 60)))
        painter.drawEllipse(QPointF(cx - 16, cy + 3), 6, 4)
        painter.drawEllipse(QPointF(cx + 16, cy + 3), 6, 4)

        # --- Mouth (omega shape) ---
        painter.setPen(QPen(QColor("#A08888"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        mouth_path = QPainterPath()
        mouth_path.moveTo(cx - 4, cy + 7)
        mouth_path.quadTo(cx - 2, cy + 12, cx, cy + 7)
        mouth_path.quadTo(cx + 2, cy + 12, cx + 4, cy + 7)
        painter.drawPath(mouth_path)

        # --- Body ---
        painter.setPen(QPen(QColor("#FF8FAB"), 1.5, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx, cy + 32), 18, 16)

        # --- Arms ---
        arm_pen = QPen(QColor("#FF8FAB"), 2, Qt.PenStyle.DashLine)
        painter.setPen(arm_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Left arm (static, resting)
        arm_left_start = QPointF(cx - 16, cy + 26)
        arm_left_end = QPointF(cx - 22, cy + 42)
        painter.drawLine(arm_left_start, arm_left_end)

        # Right arm (animated to press keys)
        arm_right_start = QPointF(cx + 16, cy + 26)
        ax, ay = self._arm_current
        # Convert arm target to widget coords (keyboard area)
        if self._arm_target:
            target_x, target_y = self._arm_target
            # Draw arm reaching toward the key
            arm_end = QPointF(target_x, min(target_y, ay + 20))
        else:
            arm_end = QPointF(cx + 22, cy + 42)

        # Draw arm as a curved line
        arm_path = QPainterPath()
        arm_path.moveTo(arm_right_start)
        mid = QPointF((arm_right_start.x() + arm_end.x()) / 2,
                       arm_right_start.y() + 10)
        arm_path.quadTo(mid, arm_end)
        painter.drawPath(arm_path)

        # Small paw circle at end of arm
        painter.setPen(QPen(QColor("#FF8FAB"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor("#FFD1DC")))
        painter.drawEllipse(arm_end, 4, 4)

    def _draw_keyboard(self, painter: QPainter):
        """Draw a cute hand-drawn QWERTY keyboard."""
        kb_x = self._kb_x
        kb_y = self._kb_y
        key_size = self._key_size
        key_unit = self._key_unit

        font = QFont("Microsoft YaHei", 7)
        painter.setFont(font)

        for label, row, col, w in _KEYBOARD_LAYOUT:
            x = kb_x + col * key_unit
            y = kb_y + row * key_unit
            w_px = w * key_size + (w - 1) * self._key_gap
            h_px = key_size

            is_pressed = label.upper() in self._pressed_keys

            # Key background
            if is_pressed:
                painter.setPen(QPen(QColor("#FF8FAB"), 2))
                painter.setBrush(QBrush(QColor(255, 143, 171, 200)))
            else:
                painter.setPen(QPen(QColor("#D6EAF8"), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor("#FFF8E7")))

            painter.drawRoundedRect(QRectF(x, y, w_px, h_px), 4, 4)

            # Key label
            display_label = " " if label == "SPACE" else label
            if is_pressed:
                painter.setPen(QColor("#FFFFFF"))
            else:
                painter.setPen(QColor("#A08888"))
            painter.drawText(QRectF(x, y, w_px, h_px),
                             Qt.AlignmentFlag.AlignCenter, display_label)
