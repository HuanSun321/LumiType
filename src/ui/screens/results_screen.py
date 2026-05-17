from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt
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


class ResultsScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()
        self._result = {}

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
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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

        # Buttons inside scrollable content
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        retry_btn = QPushButton("🔄 再来一次")
        retry_btn.setMinimumSize(180, 52)
        retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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

        menu_btn = QPushButton("🏠 返回菜单")
        menu_btn.setMinimumSize(180, 52)
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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

    def _back_to_menu(self):
        if self.navigate_to:
            self.navigate_to("menu")
