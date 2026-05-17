from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QFont, QColor, QFontMetrics, QPen, QBrush
from PyQt6.QtCore import Qt, QRect
from src.app import App
from src.constants import DEFAULT_FONT_SIZE


class TextDisplayWidget(QWidget):
    CHAR_STATE_PENDING = 0
    CHAR_STATE_CORRECT = 1
    CHAR_STATE_WRONG = 2
    CHAR_STATE_CURRENT = 3

    def __init__(self):
        super().__init__()
        self._text = ""
        self._char_states: list[int] = []
        self._cursor_pos = 0
        self._title = ""
        self._author = ""

        config = App.instance().config
        font_family = config.get("font_family") or "Microsoft YaHei"
        font_size = config.get("font_size") or DEFAULT_FONT_SIZE
        self._font = QFont(font_family, font_size)
        self._title_font = QFont(font_family, max(12, font_size - 8))
        self._line_height = font_size * 2 + 4
        self._margin = 24
        self._viewport_y = 0

        # Cached layout: list of (char_index, x, y) for each character
        self._char_positions: list[tuple[int, float, float]] = []
        self._total_height = 0

    def set_material(self, material: dict):
        self._title = material.get("title", "")
        self._author = material.get("author", "")
        self._text = material.get("content", "")
        self._char_states = [self.CHAR_STATE_PENDING] * len(self._text)
        self._cursor_pos = 0
        self._viewport_y = 0
        if self._char_states:
            self._char_states[0] = self.CHAR_STATE_CURRENT
        self._recalc_layout()
        self.update()

    @property
    def title(self) -> str:
        return self._title

    def set_cursor_position(self, pos: int):
        self._cursor_pos = pos
        self._update_viewport()
        self.update()

    def set_char_states(self, states: list[int]):
        self._char_states = states
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalc_layout()

    def _recalc_layout(self):
        """Cache character positions. Only recalculated on text change or resize."""
        fm = QFontMetrics(self._font)
        y = self._margin
        if self._title:
            y += 44
        x = self._margin
        max_x = self.width() - self._margin
        if max_x <= 0:
            max_x = 800  # fallback before widget is shown

        self._char_positions = []
        for i, ch in enumerate(self._text):
            if ch == '\n':
                self._char_positions.append((i, x, y))
                x = self._margin
                y += self._line_height
                continue
            char_width = fm.horizontalAdvance(ch)
            if x + char_width > max_x:
                x = self._margin
                y += self._line_height
            self._char_positions.append((i, x, y))
            x += char_width

        self._total_height = y + self._line_height

    def _cursor_y(self) -> float:
        """Get cursor Y from cached positions. O(1)."""
        if 0 <= self._cursor_pos < len(self._char_positions):
            return self._char_positions[self._cursor_pos][2]
        return self._margin

    def _update_viewport(self):
        if self.height() <= 0:
            return
        cursor_y = self._cursor_y()
        h = self.height()
        top = self._viewport_y + self._margin
        bottom = self._viewport_y + h * 0.6

        if cursor_y < top:
            self._viewport_y = max(0, cursor_y - self._margin)
        elif cursor_y > bottom:
            self._viewport_y = cursor_y - int(h * 0.6)

        max_offset = max(0, self._total_height - h + self._margin)
        self._viewport_y = max(0, min(self._viewport_y, max_offset))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor("#FFF8F0"))

        y = self._margin - self._viewport_y

        if self._title:
            painter.setFont(self._title_font)
            painter.setPen(QColor("#A08888"))
            title_text = f"「{self._title}」"
            if self._author:
                title_text += f" — {self._author}"
            painter.drawText(self._margin, y + 22, title_text)
            y += 44

        painter.setFont(self._font)
        fm = QFontMetrics(self._font)

        state_colors = {
            self.CHAR_STATE_PENDING: QColor("#C0B0B0"),
            self.CHAR_STATE_CORRECT: QColor("#8BD3A8"),
            self.CHAR_STATE_WRONG: QColor("#FF6B8A"),
            self.CHAR_STATE_CURRENT: QColor("#5B4A4A"),
        }

        for idx, (i, cx, cy) in enumerate(self._char_positions):
            ch = self._text[i]
            if ch == '\n':
                continue

            draw_y = cy - self._viewport_y
            if draw_y < -self._line_height or draw_y > self.height() + self._line_height:
                continue

            char_width = fm.horizontalAdvance(ch)
            state = self._char_states[i] if i < len(self._char_states) else self.CHAR_STATE_PENDING

            if state == self.CHAR_STATE_CURRENT:
                char_vis_top = draw_y + 8
                char_vis_bottom = draw_y + fm.ascent() + fm.descent() + 12
                char_vis_h = char_vis_bottom - char_vis_top
                bg_rect = QRect(int(cx) - 5, int(char_vis_top), int(char_width) + 10, int(char_vis_h))
                pen = QPen(QColor("#FFB0C8"), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(QColor("#FFE8EC")))
                painter.drawRoundedRect(bg_rect, 8, 8)
                painter.setPen(QColor("#5B4A4A"))
            elif state == self.CHAR_STATE_CORRECT:
                painter.setPen(state_colors[state])
            elif state == self.CHAR_STATE_WRONG:
                pen = QPen(QColor("#FF6B8A"), 2)
                painter.setPen(pen)
                base_y = draw_y + self._line_height - 12
                for wx in range(int(cx), int(cx + char_width), 4):
                    offset = 2 if (wx // 2) % 2 == 0 else -2
                    painter.drawLine(wx, int(base_y + offset), wx + 2, int(base_y - offset))
                painter.setPen(state_colors[state])
            else:
                painter.setPen(state_colors[state])

            painter.drawText(int(cx), int(draw_y + fm.ascent() + 10), ch)

        painter.end()
