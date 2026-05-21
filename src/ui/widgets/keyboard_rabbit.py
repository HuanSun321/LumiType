import math
import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath


# ─── Keyboard layout ───
_KEYBOARD_LAYOUT = [
    ("1", 0, 0, 1), ("2", 0, 1, 1), ("3", 0, 2, 1), ("4", 0, 3, 1), ("5", 0, 4, 1),
    ("6", 0, 5, 1), ("7", 0, 6, 1), ("8", 0, 7, 1), ("9", 0, 8, 1), ("0", 0, 9, 1),
    ("Q", 1, 0, 1), ("W", 1, 1, 1), ("E", 1, 2, 1), ("R", 1, 3, 1), ("T", 1, 4, 1),
    ("Y", 1, 5, 1), ("U", 1, 6, 1), ("I", 1, 7, 1), ("O", 1, 8, 1), ("P", 1, 9, 1),
    ("A", 2, 0.5, 1), ("S", 2, 1.5, 1), ("D", 2, 2.5, 1), ("F", 2, 3.5, 1), ("G", 2, 4.5, 1),
    ("H", 2, 5.5, 1), ("J", 2, 6.5, 1), ("K", 2, 7.5, 1), ("L", 2, 8.5, 1),
    ("Z", 3, 1, 1), ("X", 3, 2, 1), ("C", 3, 3, 1), ("V", 3, 4, 1), ("B", 3, 5, 1),
    ("N", 3, 6, 1), ("M", 3, 7, 1),
    ("SPACE", 4, 2, 5),
]
_KEY_MAP = {}
for label, row, col, w in _KEYBOARD_LAYOUT:
    _KEY_MAP[label.upper()] = (row, col + w / 2.0, w)


# ─── SpringBone physics ───
class SpringBone:
    """A single spring-damped bone node for physics-based animation."""

    def __init__(self, rest_x: float, rest_y: float,
                 stiffness: float = 0.1, damping: float = 0.88):
        self.rest_x = rest_x
        self.rest_y = rest_y
        self.x = rest_x
        self.y = rest_y
        self.vx = 0.0
        self.vy = 0.0
        self.stiffness = stiffness
        self.damping = damping
        self.target_x = None  # override target (e.g. key position)
        self.target_y = None

    def set_target(self, x: float | None, y: float | None):
        self.target_x = x
        self.target_y = y

    def update(self, dt: float = 1.0):
        # Use target if set, otherwise rest position
        tx = self.target_x if self.target_x is not None else self.rest_x
        ty = self.target_y if self.target_y is not None else self.rest_y

        fx = (tx - self.x) * self.stiffness
        fy = (ty - self.y) * self.stiffness
        self.vx = (self.vx + fx) * self.damping
        self.vy = (self.vy + fy) * self.damping
        self.x += self.vx * dt
        self.y += self.vy * dt

    def perturb(self, dx: float, dy: float):
        """Add a small perturbation (for idle animation)."""
        self.vx += dx
        self.vy += dy


# ─── Expression system ───
_EXPR_IDLE = "idle"
_EXPR_HAPPY = "happy"
_EXPR_WRONG = "wrong"
_EXPR_COMBO = "combo"


def _color(name: str, alpha: int | None = None) -> QColor:
    color = QColor(name)
    if alpha is not None:
        color.setAlpha(alpha)
    return color


class KeyboardRabbitWidget(QWidget):
    """Live2D-style hand-drawn rabbit with spring physics + expression system."""

    BASE_WIDTH = 320
    BASE_HEIGHT = 220

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale_percent = 75
        self._paint_opacity = 0.9
        self.set_scale_percent(self._scale_percent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # ── Spring bones ──
        # Body center: (160, 97)
        # Head center: (160, 65)
        self._left_ear = SpringBone(145, 27, stiffness=0.08, damping=0.88)
        self._right_ear = SpringBone(175, 27, stiffness=0.08, damping=0.88)
        self._head = SpringBone(160, 65, stiffness=0.12, damping=0.90)
        self._right_arm = SpringBone(182, 107, stiffness=0.15, damping=0.85)

        # ── Animation state ──
        self._pressed_keys: set[str] = set()
        self._expression = _EXPR_IDLE
        self._expr_timer = QTimer(self)
        self._expr_timer.setSingleShot(True)
        self._expr_timer.setInterval(1500)
        self._expr_timer.timeout.connect(self._reset_expression)
        self._breath_phase = 0.0
        self._idle_phase = 0.0

        # ── Main animation timer (60fps) ──
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start()

        # ── Keyboard geometry ──
        self._kb_x = 20
        self._kb_y = 130
        self._key_size = 22
        self._key_gap = 2
        self._key_unit = self._key_size + self._key_gap

    # ── Public API ──

    def highlight_pinyin(self, pinyin: str):
        """Highlight keys matching the current composing pinyin string."""
        self._pressed_keys.clear()
        if pinyin:
            for ch in pinyin.upper():
                if ch.isalpha() or ch in _KEY_MAP:
                    self._pressed_keys.add(ch)
            last_ch = pinyin[-1].upper()
            pos = self._get_key_center(last_ch)
            if pos:
                self._right_arm.set_target(pos[0], pos[1])
        else:
            self._right_arm.set_target(None, None)
        self.update()

    def clear_highlights(self):
        self._pressed_keys.clear()
        self._right_arm.set_target(None, None)
        self.update()

    def set_expression(self, expr: str):
        """Set rabbit expression: idle, happy, wrong, combo."""
        self._expression = expr
        self._expr_timer.stop()
        if expr != _EXPR_COMBO:
            self._expr_timer.start()
        self.update()

    def set_scale_percent(self, value: int):
        self._scale_percent = max(60, min(140, int(value)))
        self.setFixedSize(
            int(self.BASE_WIDTH * self._scale_percent / 100),
            int(self.BASE_HEIGHT * self._scale_percent / 100),
        )
        self.update()

    def set_preview_opacity(self, value: float):
        self._paint_opacity = max(0.15, min(1.0, float(value)))
        self.update()

    # ── Animation loop ──

    def _animate(self):
        try:
            self._breath_phase += 0.033  # ~3s cycle at 60fps
            self._idle_phase += 0.05     # idle ear sway

            # Idle perturbation for ears
            ear_perturb_x = math.sin(self._idle_phase) * 0.15
            ear_perturb_y = math.cos(self._idle_phase * 0.7) * 0.08
            self._left_ear.perturb(ear_perturb_x, ear_perturb_y)
            self._right_ear.perturb(-ear_perturb_x, ear_perturb_y)

            # Head follows right arm direction slightly
            arm_dx = self._right_arm.x - self._right_arm.rest_x
            head_offset_x = arm_dx * 0.08  # subtle lean
            self._head.set_target(self._head.rest_x + head_offset_x, None)

            # Update all bones
            self._left_ear.update()
            self._right_ear.update()
            self._head.update()
            self._right_arm.update()

            self.update()
        except Exception as e:
            import traceback
            with open("crash.log", "a", encoding="utf-8") as f:
                f.write(f"\n--- ANIMATE ERROR: {e} ---\n")
                traceback.print_exc(file=f)
            self._anim_timer.stop()

    def _reset_expression(self):
        self._expression = _EXPR_IDLE
        self.update()

    # ── Keyboard helpers ──

    def _get_key_center(self, key: str) -> tuple[float, float] | None:
        info = _KEY_MAP.get(key.upper())
        if not info:
            return None
        row, col_center, w = info
        x = self._kb_x + col_center * self._key_unit
        y = self._kb_y + row * self._key_unit + self._key_size / 2
        return (x, y)

    # ── Paint ──

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._paint_opacity)
        painter.scale(self.width() / self.BASE_WIDTH, self.height() / self.BASE_HEIGHT)

        # Body center with breathing
        body_cx = 160
        body_cy = 97 + math.sin(self._breath_phase) * 1.5

        # Draw rabbit
        self._draw_body(painter, body_cx, body_cy)
        hx, hy = self._head.x, self._head.y
        self._draw_head(painter, hx, hy)
        self._draw_ears(painter, hx, hy)
        self._draw_face(painter, hx, hy)
        self._draw_effects(painter, hx, hy)
        self._draw_arms(painter, body_cx, body_cy)

        # Draw keyboard
        self._draw_keyboard(painter)

        painter.end()

    # ── Rabbit parts ──

    def _draw_body(self, painter: QPainter, cx: float, cy: float):
        pen = QPen(QColor("#FF8FAB"), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx, cy), 18, 16)

    def _draw_head(self, painter: QPainter, cx: float, cy: float):
        pen = QPen(QColor("#FF8FAB"), 1.5, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx, cy), 22, 20)

    def _draw_ears(self, painter: QPainter, hx: float, hy: float):
        ear_pen = QPen(QColor("#FF8FAB"), 1.5, Qt.PenStyle.DashLine)
        ear_fill = QBrush(QColor("#FFFFFF"))
        inner_fill = QBrush(QColor("#FFD1DC"))

        # Left ear (spring-driven)
        lx, ly = self._left_ear.x, self._left_ear.y
        painter.setPen(ear_pen)
        painter.setBrush(ear_fill)
        painter.drawEllipse(QPointF(lx, ly), 8, 22)
        painter.setBrush(inner_fill)
        painter.drawEllipse(QPointF(lx, ly + 2), 5, 16)

        # Right ear (spring-driven)
        rx, ry = self._right_ear.x, self._right_ear.y
        painter.setPen(ear_pen)
        painter.setBrush(ear_fill)
        painter.drawEllipse(QPointF(rx, ry), 8, 22)
        painter.setBrush(inner_fill)
        painter.drawEllipse(QPointF(rx, ry + 2), 5, 16)

    def _draw_face(self, painter: QPainter, cx: float, cy: float):
        expr = self._expression
        # Eyes
        if expr == _EXPR_HAPPY:
            self._draw_eyes_happy(painter, cx, cy)
        elif expr == _EXPR_WRONG:
            self._draw_eyes_wrong(painter, cx, cy)
        elif expr == _EXPR_COMBO:
            self._draw_eyes_combo(painter, cx, cy)
        else:
            self._draw_eyes_idle(painter, cx, cy)

        # Blush
        if expr == _EXPR_WRONG:
            pass  # no blush
        elif expr == _EXPR_COMBO:
            self._draw_blush_combo(painter, cx, cy)
        elif expr == _EXPR_HAPPY:
            self._draw_blush_happy(painter, cx, cy)
        else:
            self._draw_blush_idle(painter, cx, cy)

        # Mouth
        if expr == _EXPR_HAPPY:
            self._draw_mouth_happy(painter, cx, cy)
        elif expr == _EXPR_WRONG:
            self._draw_mouth_wrong(painter, cx, cy)
        elif expr == _EXPR_COMBO:
            self._draw_mouth_combo(painter, cx, cy)
        else:
            self._draw_mouth_idle(painter, cx, cy)

    # ── Eyes ──

    def _draw_eyes_idle(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#5B4A4A")))
        painter.drawEllipse(QPointF(cx - 8, cy - 3), 3, 3)
        painter.drawEllipse(QPointF(cx + 8, cy - 3), 3, 3)
        # Highlights
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(QPointF(cx - 7, cy - 4), 1.5, 1.5)
        painter.drawEllipse(QPointF(cx + 9, cy - 4), 1.5, 1.5)

    def _draw_eyes_happy(self, painter: QPainter, cx: float, cy: float):
        # Star eyes
        painter.setPen(QPen(QColor("#FFD700"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor("#FFE066")))
        self._draw_star_shape(painter, cx - 8, cy - 3, 4)
        self._draw_star_shape(painter, cx + 8, cy - 3, 4)

    def _draw_eyes_wrong(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#5B4A4A")))
        painter.drawEllipse(QPointF(cx - 8, cy - 3), 2, 2)
        painter.drawEllipse(QPointF(cx + 8, cy - 3), 2, 2)

    def _draw_eyes_combo(self, painter: QPainter, cx: float, cy: float):
        # Big eyes + star highlight
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#5B4A4A")))
        painter.drawEllipse(QPointF(cx - 8, cy - 3), 4, 4)
        painter.drawEllipse(QPointF(cx + 8, cy - 3), 4, 4)
        painter.setBrush(QBrush(QColor("#FFE066")))
        self._draw_star_shape(painter, cx - 7, cy - 4, 2)
        self._draw_star_shape(painter, cx + 9, cy - 4, 2)

    # ── Mouth ──

    def _draw_mouth_idle(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(QPen(QColor("#A08888"), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(cx - 4, cy + 7)
        path.quadTo(cx - 2, cy + 12, cx, cy + 7)
        path.quadTo(cx + 2, cy + 12, cx + 4, cy + 7)
        painter.drawPath(path)

    def _draw_mouth_happy(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(QPen(QColor("#A08888"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(cx - 5, cy + 8)
        path.quadTo(cx, cy + 14, cx + 5, cy + 8)
        painter.drawPath(path)

    def _draw_mouth_wrong(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(QPen(QColor("#A08888"), 1.2))
        painter.drawLine(QPointF(cx - 3, cy + 9), QPointF(cx + 3, cy + 9))

    def _draw_mouth_combo(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(QPen(QColor("#A08888"), 1.5))
        painter.setBrush(QBrush(QColor("#FFD1DC")))
        path = QPainterPath()
        path.moveTo(cx - 6, cy + 7)
        path.quadTo(cx, cy + 16, cx + 6, cy + 7)
        painter.drawPath(path)

    # ── Blush ──

    def _draw_blush_idle(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 182, 193, 60)))
        painter.drawEllipse(QPointF(cx - 16, cy + 3), 6, 4)
        painter.drawEllipse(QPointF(cx + 16, cy + 3), 6, 4)

    def _draw_blush_happy(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 182, 193, 100)))
        painter.drawEllipse(QPointF(cx - 16, cy + 3), 7, 5)
        painter.drawEllipse(QPointF(cx + 16, cy + 3), 7, 5)

    def _draw_blush_combo(self, painter: QPainter, cx: float, cy: float):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 143, 171, 120)))
        painter.drawEllipse(QPointF(cx - 16, cy + 3), 8, 5)
        painter.drawEllipse(QPointF(cx + 16, cy + 3), 8, 5)

    # ── Effects ──

    def _draw_effects(self, painter: QPainter, cx: float, cy: float):
        if self._expression == _EXPR_WRONG:
            self._draw_sweat_drop(painter, cx + 22, cy - 10)
        elif self._expression == _EXPR_COMBO:
            self._draw_fire(painter, cx - 10, cy - 22)
            self._draw_fire(painter, cx + 10, cy - 22)

    def _draw_sweat_drop(self, painter: QPainter, x: float, y: float):
        painter.setPen(QPen(QColor("#AED6F1"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(_color("#D6EAF8", 180)))
        # Teardrop shape
        path = QPainterPath()
        path.moveTo(x, y - 4)
        path.quadTo(x + 3, y, x, y + 4)
        path.quadTo(x - 3, y, x, y - 4)
        painter.drawPath(path)

    def _draw_fire(self, painter: QPainter, x: float, y: float):
        painter.setPen(QPen(QColor("#FFB86C"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(_color("#FF8FAB", 150)))
        # Small flame triangle
        path = QPainterPath()
        path.moveTo(x, y - 6)
        path.lineTo(x - 3, y + 2)
        path.lineTo(x + 3, y + 2)
        path.closeSubpath()
        painter.drawPath(path)
        # Inner flame
        painter.setBrush(QBrush(_color("#FFD700", 120)))
        path2 = QPainterPath()
        path2.moveTo(x, y - 3)
        path2.lineTo(x - 1.5, y + 1)
        path2.lineTo(x + 1.5, y + 1)
        path2.closeSubpath()
        painter.drawPath(path2)

    # ── Arms ──

    def _draw_arms(self, painter: QPainter, body_cx: float, body_cy: float):
        arm_pen = QPen(QColor("#FF8FAB"), 2, Qt.PenStyle.DashLine)
        painter.setPen(arm_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Left arm (static, resting)
        left_start = QPointF(body_cx - 16, body_cy - 6)
        left_end = QPointF(body_cx - 22, body_cy + 10)
        painter.drawLine(left_start, left_end)
        # Paw
        painter.setPen(QPen(QColor("#FF8FAB"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor("#FFD1DC")))
        painter.drawEllipse(left_end, 4, 4)

        # Right arm (spring-driven)
        right_start = QPointF(body_cx + 16, body_cy - 6)
        ax, ay = self._right_arm.x, self._right_arm.y
        if self._right_arm.target_x is not None:
            arm_end = QPointF(ax, min(ay, ay + 5))
        else:
            arm_end = QPointF(ax, ay)

        # Curved arm path
        arm_path = QPainterPath()
        arm_path.moveTo(right_start)
        mid = QPointF((right_start.x() + arm_end.x()) / 2,
                       right_start.y() + 8)
        arm_path.quadTo(mid, arm_end)
        painter.setPen(arm_pen)
        painter.drawPath(arm_path)

        # Paw
        painter.setPen(QPen(QColor("#FF8FAB"), 1, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor("#FFD1DC")))
        painter.drawEllipse(arm_end, 4, 4)

    # ── Star shape helper ──

    def _draw_star_shape(self, painter: QPainter, cx: float, cy: float, size: float):
        path = QPainterPath()
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            outer = QPointF(cx + math.cos(angle) * size,
                           cy + math.sin(angle) * size)
            inner_angle = math.radians(i * 72 + 36 - 90)
            inner = QPointF(cx + math.cos(inner_angle) * size * 0.4,
                           cy + math.sin(inner_angle) * size * 0.4)
            if i == 0:
                path.moveTo(outer)
            else:
                path.lineTo(outer)
            path.lineTo(inner)
        path.closeSubpath()
        painter.drawPath(path)

    # ── Keyboard ──

    def _draw_keyboard(self, painter: QPainter):
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

            if is_pressed:
                painter.setPen(QPen(QColor("#FF8FAB"), 2))
                painter.setBrush(QBrush(QColor(255, 143, 171, 200)))
            else:
                painter.setPen(QPen(QColor("#D6EAF8"), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor("#FFF8E7")))

            painter.drawRoundedRect(QRectF(x, y, w_px, h_px), 4, 4)

            display_label = " " if label == "SPACE" else label
            if is_pressed:
                painter.setPen(QColor("#FFFFFF"))
            else:
                painter.setPen(QColor("#A08888"))
            painter.drawText(QRectF(x, y, w_px, h_px),
                             Qt.AlignmentFlag.AlignCenter, display_label)
