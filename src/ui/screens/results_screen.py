from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, QEvent
from src.constants import (
    COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH, COLOR_SKY, COLOR_ERROR,
)


def _stat_card(label: str, value: str, emoji: str, bg: str) -> QWidget:
    card = QWidget()
    card.setStyleSheet(f"""
        background-color: {bg};
        border: 2px dashed {COLOR_PINK_LIGHT};
        border-radius: 16px;
    """)
    card_layout = QVBoxLayout(card)
    card_layout.setSpacing(4)
    card_layout.setContentsMargins(16, 14, 16, 14)

    emoji_lbl = QLabel(emoji)
    emoji_lbl.setStyleSheet("font-size: 24px; background: transparent; border: none;")
    emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card_layout.addWidget(emoji_lbl)

    val = QLabel(value)
    val.setStyleSheet(f"color: #5B4A4A; font-size: 24px; font-weight: bold; background: transparent; border: none;")
    val.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card_layout.addWidget(val)

    lbl = QLabel(label)
    lbl.setStyleSheet(f"color: #A08888; font-size: 13px; background: transparent; border: none;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card_layout.addWidget(lbl)
    return card


def _mistake_counts(mistakes: list[dict]) -> list[tuple[str, int, str]]:
    counts: dict[str, dict] = {}
    for event in mistakes:
        expected = event.get("expected", "")
        if not expected:
            continue
        item = counts.setdefault(expected, {"count": 0, "actual": event.get("actual", "")})
        item["count"] += 1
        if event.get("actual"):
            item["actual"] = event.get("actual", "")
    return sorted(
        ((ch, data["count"], data["actual"]) for ch, data in counts.items()),
        key=lambda row: (-row[1], row[0]),
    )


class ResultsScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()
        self._result = {}
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def eventFilter(self, obj, ev):
        # Block space/enter on all child buttons to prevent accidental clicks
        if ev.type() == QEvent.Type.KeyPress and isinstance(obj, QPushButton):
            if ev.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                return True
        return super().eventFilter(obj, ev)

    def _install_button_filter(self, btn: QPushButton):
        btn.setAutoDefault(False)
        btn.setDefault(False)
        btn.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        btn.installEventFilter(self)

    def on_enter(self, data: dict):
        self._result = data
        self._build_ui()

    def _build_ui(self):
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
        else:
            layout = QVBoxLayout(self)

        layout.setSpacing(12)
        layout.setContentsMargins(36, 16, 36, 16)

        # Top bar with back button (always visible)
        top_bar = QHBoxLayout()
        back_btn = QPushButton("← 返回主菜单")
        back_btn.setObjectName("back_btn")
        back_btn.setFixedHeight(36)
        self._install_button_filter(back_btn)
        back_btn.clicked.connect(self._back_to_menu)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)

        # Scroll area for content (handles small windows)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(14)
        content_layout.setContentsMargins(0, 8, 0, 8)

        # Title
        title = QLabel("🎉 练习完成！")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 34px; font-weight: bold; color: {COLOR_ACCENT}; background: transparent;")
        content_layout.addWidget(title)

        # Performance message
        accuracy = self._result.get("accuracy", 0)
        if accuracy >= 0.95:
            msg = "太棒了！完美表现~ ⭐"
        elif accuracy >= 0.8:
            msg = "做得很好！继续加油~ 💪"
        elif accuracy >= 0.6:
            msg = "还不错哦~ 多练习就好啦 🌸"
        else:
            msg = "别灰心~ 下次一定更好！🌈"
        subtitle = QLabel(msg)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #A08888; background: transparent;")
        content_layout.addWidget(subtitle)

        content_layout.addSpacing(4)

        # Stats grid
        mode = self._result.get("mode", "")
        mode_names = {"follow": "跟打练习", "falling": "掉落消除", "timed": "限时挑战"}
        mode_display = mode_names.get(mode, mode)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)
        stats_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cards = [
            ("模式", mode_display, "🎮", COLOR_LAVENDER),
            ("积分", str(self._result.get("score", 0)), "✨", COLOR_CREAM),
            ("CPM", f"{self._result.get('cpm', 0):.1f}", "⚡", COLOR_SKY),
            ("正确率", f"{self._result.get('accuracy', 0):.0%}", "🎯", COLOR_MINT),
            ("最大连击", str(self._result.get("max_combo", 0)), "🔥", COLOR_PEACH),
            ("用时", f"{self._result.get('elapsed', 0):.0f}s", "⏰", COLOR_PINK_LIGHT),
        ]

        for label, value, emoji, bg in cards:
            stats_layout.addWidget(_stat_card(label, value, emoji, bg))

        content_layout.addLayout(stats_layout)
        content_layout.addSpacing(16)

        mistakes = self._result.get("mistakes", [])
        review_box = QFrame()
        review_box.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_CREAM};
                border: 2px dashed {COLOR_PINK_LIGHT};
                border-radius: 16px;
            }}
        """)
        review_layout = QVBoxLayout(review_box)
        review_layout.setContentsMargins(18, 12, 18, 12)
        review_layout.setSpacing(6)

        review_title = QLabel("🧭 本次复盘")
        review_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_ACCENT}; background: transparent;")
        review_layout.addWidget(review_title)

        top_mistakes = _mistake_counts(mistakes)[:8]
        if top_mistakes:
            parts = []
            for expected, count, actual in top_mistakes:
                suffix = f"（误输 {actual}）" if actual else ""
                parts.append(f"{expected} ×{count}{suffix}")
            review_text = "常错：" + "  ".join(parts)
        else:
            review_text = "本次没有错字，保持这个手感。"
        review_label = QLabel(review_text)
        review_label.setWordWrap(True)
        review_label.setStyleSheet("font-size: 14px; color: #5B4A4A; background: transparent;")
        review_layout.addWidget(review_label)
        content_layout.addWidget(review_box)
        content_layout.addSpacing(8)

        # Buttons inside scrollable content
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        retry_btn = QPushButton("🔄 再来一次")
        retry_btn.setMinimumSize(180, 52)
        self._install_button_filter(retry_btn)
        retry_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: 2px solid {COLOR_ACCENT};
                border-radius: 18px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ff7096;
                border-color: #ff7096;
            }}
        """)
        retry_btn.clicked.connect(self._retry)
        btn_layout.addWidget(retry_btn)

        if top_mistakes:
            review_btn = QPushButton("🎯 重练错字")
            review_btn.setMinimumSize(180, 52)
            self._install_button_filter(review_btn)
            review_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_MINT};
                    color: #5B4A4A;
                    border: 2px solid {COLOR_PINK_LIGHT};
                    border-radius: 18px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACCENT};
                    color: #ffffff;
                }}
            """)
            review_btn.clicked.connect(self._review_mistakes)
            btn_layout.addWidget(review_btn)

        menu_btn = QPushButton("🏠 返回菜单")
        menu_btn.setMinimumSize(180, 52)
        self._install_button_filter(menu_btn)
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_LAVENDER};
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 18px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
            }}
        """)
        menu_btn.clicked.connect(self._back_to_menu)
        btn_layout.addWidget(menu_btn)

        content_layout.addLayout(btn_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _retry(self):
        mode = self._result.get("mode", "follow")
        if self.navigate_to:
            self.navigate_to("game", {"mode": mode})

    def _review_mistakes(self):
        mistakes = _mistake_counts(self._result.get("mistakes", []))
        chars = [expected for expected, _, _ in mistakes]
        if not chars:
            return
        text = "".join(chars)
        while len(text) < min(24, len(chars) * 4):
            text += "".join(chars)
        material = {
            "title": "本次错字复训",
            "author": "",
            "category": "review",
            "content": text[:80],
            "difficulty": 1,
            "source": "session_mistakes",
        }
        if self.navigate_to:
            self.navigate_to("game", {"mode": "follow", "material": material})

    def _back_to_menu(self):
        if self.navigate_to:
            self.navigate_to("menu")
