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
        self._category = ""

        config = App.instance().config
        font_family = config.get("font_family") or "Microsoft YaHei"
        font_size = config.get("font_size") or DEFAULT_FONT_SIZE
        self._font = QFont(font_family, font_size)
        self._title_font = QFont(font_family, max(12, font_size - 8))
        self._line_height = font_size * 2 + 4
        self._margin = 24
        self._viewport_y = 0

        # Layout mode: 'poetry' | 'prose'
        self._layout_mode = "prose"

        # Cached layout: list of (char_index, x, y)
        self._char_positions: list[tuple[int, float, float]] = []
        self._total_height = 0

    def set_material(self, material: dict):
        self._title = material.get("title", "")
        self._author = material.get("author", "")
        self._text = material.get("content", "")
        self._category = material.get("category", "")
        self._char_states = [self.CHAR_STATE_PENDING] * len(self._text)
        self._cursor_pos = 0
        self._viewport_y = 0
        if self._char_states:
            self._char_states[0] = self.CHAR_STATE_CURRENT
        self._detect_mode()
        self._recalc_layout()
        self.update()

    def _detect_mode(self):
        """Detect if text is poetry (short lines with \\n) or prose."""
        # If material explicitly tagged as poetry, force poetry mode
        if self._category in ("poetry", "poem"):
            self._layout_mode = "poetry"
            return
        lines = self._text.split('\n')
        if len(lines) <= 1:
            self._layout_mode = "prose"
            return
        # Poetry: most lines are short (≤10 chars, typical 五言/七言)
        avg_len = sum(len(l) for l in lines) / len(lines)
        self._layout_mode = "poetry" if avg_len <= 10 else "prose"

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
        fm = QFontMetrics(self._font)
        max_x = self.width() - self._margin
        if max_x <= 0:
            max_x = 800

        if self._layout_mode == "poetry":
            self._recalc_poetry(fm, self._margin, max_x)
        else:
            self._recalc_prose(fm, self._margin, max_x)

    def _recalc_poetry(self, fm, y, max_x):
        """Center each line of poetry both horizontally and vertically."""
        self._char_positions = []
        lines = self._text.split('\n')

        # Calculate total content height for vertical centering
        title_height = 44 if self._title else 0
        content_height = len(lines) * self._line_height
        total_content = title_height + content_height
        widget_h = self.height() if self.height() > 100 else 600
        vertical_offset = max(0, (widget_h - total_content) / 2)

        y = vertical_offset
        if self._title:
            y += title_height

        char_idx = 0
        for line_idx, line in enumerate(lines):
            line_width = sum(fm.horizontalAdvance(ch) for ch in line)
            line_x = self._margin + max(0, (max_x - self._margin * 2 - line_width) / 2)
            x = line_x
            for ch in line:
                self._char_positions.append((char_idx, x, y))
                x += fm.horizontalAdvance(ch)
                char_idx += 1
            char_idx += 1  # skip \n
            y += self._line_height

        self._total_height = max(widget_h, y + self._line_height)
        self._poetry_vertically_centered = total_content <= widget_h

    def _recalc_prose(self, fm, y, max_x):
        """Prose: indent first line of each paragraph, extra spacing between paragraphs."""
        self._char_positions = []
        indent_width = fm.horizontalAdvance('　') * 2  # 2 full-width spaces
        paragraph_gap = self._line_height * 0.6  # extra space between paragraphs
        lines = self._text.split('\n')

        # If the text has no newlines at all (single paragraph), still indent first line
        is_single_para = len(lines) <= 1

        char_idx = 0
        # Start with title offset
        y = self._margin
        if self._title:
            y += 44

        for line_idx, line in enumerate(lines):
            # First line of each paragraph gets indent
            if line_idx == 0:
                x = self._margin + indent_width
            else:
                x = self._margin + indent_width

            for ch in line:
                ch_w = fm.horizontalAdvance(ch)
                if x + ch_w > max_x:
                    x = self._margin  # wrap: no indent on continuation lines
                    y += self._line_height
                self._char_positions.append((char_idx, x, y))
                x += ch_w
                char_idx += 1
            char_idx += 1  # skip \n
            y += self._line_height
            # Extra gap between paragraphs (not after last)
            if line_idx < len(lines) - 1:
                y += paragraph_gap

        self._total_height = y + self._line_height

    def _cursor_y(self) -> float:
        if 0 <= self._cursor_pos < len(self._char_positions):
            return self._char_positions[self._cursor_pos][2]
        return self._margin

    def _update_viewport(self):
        if self.height() <= 0:
            return
        # Disable scrolling when poetry fits vertically
        if getattr(self, '_poetry_vertically_centered', False):
            self._viewport_y = 0
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

        # For vertically centered poetry, compute title position from char_positions
        if self._layout_mode == "poetry" and getattr(self, '_poetry_vertically_centered', False):
            if self._title and self._char_positions:
                # Title sits above the first character line
                first_char_y = self._char_positions[0][2]
                y = first_char_y - 44 - self._viewport_y
            elif self._title:
                y = self._margin - self._viewport_y

        if self._title:
            painter.setFont(self._title_font)
            painter.setPen(QColor("#A08888"))
            title_text = f"「{self._title}」"
            if self._author:
                title_text += f" — {self._author}"
            # Center title
            title_width = QFontMetrics(self._title_font).horizontalAdvance(title_text)
            title_x = self._margin + max(0, (self.width() - self._margin * 2 - title_width) / 2)
            painter.drawText(int(title_x), int(y + 22), title_text)
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
