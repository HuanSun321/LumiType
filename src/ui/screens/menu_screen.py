from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from src.core.game_state import GameMode
from src.app import App
from src.constants import (
    COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH, COLOR_SKY,
)


class ModeCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, mode: str, title: str, description: str, emoji: str = "", bg_color: str = COLOR_CREAM):
        super().__init__()
        self.setObjectName("card")
        self.setFixedSize(220, 200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mode = mode

        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {bg_color};
                border: 2px dashed {COLOR_PINK_LIGHT};
                border-radius: 20px;
                padding: 16px;
            }}
            QFrame#card:hover {{
                border: 2px dashed {COLOR_ACCENT};
                background-color: #fff0f3;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        if emoji:
            emoji_label = QLabel(emoji)
            emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            emoji_label.setStyleSheet("font-size: 42px; background: transparent; border: none;")
            layout.addWidget(emoji_label)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: #5B4A4A; background: transparent; border: none;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setStyleSheet("font-size: 13px; color: #A08888; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self._mode)
        super().mousePressEvent(event)


class MenuScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)

        # Title area
        title = QLabel("逐字拾光")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 42px; font-weight: bold; color: {COLOR_ACCENT};")
        layout.addWidget(title)

        subtitle = QLabel(" 一起来练打字吧~ ")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #A08888;")
        layout.addWidget(subtitle)

        layout.addSpacing(4)

        today_btn = QPushButton("🌱 今日练习")
        today_btn.setFixedSize(220, 50)
        today_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: 2px solid {COLOR_ACCENT};
                border-radius: 18px;
                padding: 8px 24px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ff7096;
                border-color: #ff7096;
            }}
        """)
        today_btn.clicked.connect(self._start_today_training)
        layout.addWidget(today_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Category selector
        cat_row = QHBoxLayout()
        cat_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat_row.setSpacing(10)

        cat_label = QLabel("📚 素材来源：")
        cat_label.setStyleSheet("font-size: 15px; color: #5B4A4A; background: transparent; border: none;")
        cat_row.addWidget(cat_label)

        self._cat_combo = QComboBox()
        self._cat_combo.addItems(["全部", "诗词", "成语", "文章", "新闻", "法律"])
        self._cat_combo.setFixedWidth(130)
        self._cat_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLOR_CREAM};
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 14px;
            }}
            QComboBox:hover {{ border-color: {COLOR_ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background-color: #fff;
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 8px;
                selection-background-color: {COLOR_ACCENT};
                selection-color: #fff;
            }}
        """)
        cat_row.addWidget(self._cat_combo)
        layout.addLayout(cat_row)

        layout.addSpacing(4)

        # Mode cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        modes = [
            (GameMode.FOLLOW_TYPING.value, "跟打练习", "逐字跟打原文\n看看你的速度~", "📖", COLOR_CREAM),
            (GameMode.FALLING_TEXT.value, "掉落消除", "字符从天而降\n快快消灭它们!", "🌧️", COLOR_SKY),
            (GameMode.TIMED_CHALLENGE.value, "限时挑战", "限时冲刺模式\n连击加分哦!", "⏱️", COLOR_PEACH),
        ]
        for mode_id, title_text, desc, emoji, bg in modes:
            card = ModeCard(mode_id, title_text, desc, emoji, bg)
            card.clicked.connect(self._on_mode_selected)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        layout.addSpacing(8)

        # Bottom navigation
        nav_layout = QHBoxLayout()
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.setSpacing(16)

        nav_btns = [
            ("📊 历史记录", "stats", COLOR_LAVENDER),
            ("📚 素材库", "material", COLOR_MINT),
            ("⚙️ 设置", "settings", COLOR_PEACH),
        ]
        for text, target, bg in nav_btns:
            btn = QPushButton(text)
            btn.setFixedSize(140, 44)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: #5B4A4A;
                    border: 2px solid {COLOR_PINK_LIGHT};
                    border-radius: 14px;
                    padding: 8px 20px;
                    font-size: 15px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACCENT};
                    color: #ffffff;
                    border-color: {COLOR_ACCENT};
                }}
            """)
            btn.clicked.connect(lambda checked, t=target: self.navigate_to(t) if self.navigate_to else None)
            nav_layout.addWidget(btn)

        layout.addLayout(nav_layout)

    def _get_category(self) -> str | None:
        cat_map = {"全部": None, "诗词": "poetry", "成语": "idiom", "文章": "article", "新闻": "news", "法律": "legal"}
        return cat_map.get(self._cat_combo.currentText())

    def _on_mode_selected(self, mode: str):
        category = self._get_category()
        config_ratio = App.instance().config.get("content_ratio")
        ratio = config_ratio / 100.0 if config_ratio else 1.0

        if self.navigate_to:
            self.navigate_to("game", {
                "mode": mode,
                "category": category,
                "ratio": ratio,
            })

    def _start_today_training(self):
        category = self._get_category()
        config_ratio = App.instance().config.get("content_ratio")
        ratio = config_ratio / 100.0 if config_ratio else 1.0
        review_material = App.instance().db.build_review_material()

        data = {
            "mode": GameMode.FOLLOW_TYPING.value,
            "category": category,
            "ratio": ratio,
        }
        if review_material:
            data["material"] = review_material
            data["category"] = None
            data["ratio"] = 1.0

        if self.navigate_to:
            self.navigate_to("game", data)

    def on_enter(self, data: dict):
        pass
