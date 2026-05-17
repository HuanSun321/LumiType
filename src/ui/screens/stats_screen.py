from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt
from src.app import App
from src.constants import (
    COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH, COLOR_SKY, COLOR_ERROR,
)


def _summary_card(label_text: str, value_text: str, emoji: str, bg: str) -> QVBoxLayout:
    card = QVBoxLayout()
    card.setSpacing(2)
    emoji_lbl = QLabel(emoji)
    emoji_lbl.setStyleSheet("font-size: 20px;")
    emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card.addWidget(emoji_lbl)
    value = QLabel(value_text)
    value.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLOR_ACCENT};")
    value.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card.addWidget(value)
    label = QLabel(label_text)
    label.setStyleSheet(f"font-size: 13px; color: #A08888;")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card.addWidget(label)
    return card


class StatsScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()

    def on_enter(self, data: dict):
        self._build_ui()

    def _build_ui(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(36, 24, 36, 24)

        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.setObjectName("back_btn")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.navigate_to("menu") if self.navigate_to else None)
        header.addWidget(back_btn)
        header.addStretch()
        title = QLabel("📊 历史记录")
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLOR_ACCENT};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Summary stats
        summary = self._get_summary()
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(24)
        summary_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_configs = [
            ("总练习次数", "📝", COLOR_LAVENDER),
            ("平均 CPM", "⚡", COLOR_SKY),
            ("平均正确率", "🎯", COLOR_MINT),
            ("最高积分", "✨", COLOR_CREAM),
            ("最高连击", "🔥", COLOR_PEACH),
        ]
        for (label_text, value_text), (_, emoji, bg) in zip(summary, card_configs):
            summary_layout.addLayout(_summary_card(label_text, value_text, emoji, bg))

        layout.addLayout(summary_layout)

        # History table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "时间", "模式", "CPM", "正确率", "积分", "最高连击", "素材"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self._load_history()
        layout.addWidget(self._table)

        # Clear button
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        clear_btn = QPushButton("🗑️ 清空历史记录")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFE0E0;
                color: #C06060;
                border: 2px solid #FFD1DC;
                border-radius: 14px;
                padding: 8px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                color: #ffffff;
                border-color: {COLOR_ERROR};
            }}
        """)
        clear_btn.clicked.connect(self._clear_history)
        bottom_bar.addWidget(clear_btn)
        layout.addLayout(bottom_bar)

    def _get_summary(self) -> list[tuple[str, str]]:
        db = App.instance().db
        try:
            row = db.conn.execute("""
                SELECT COUNT(*),
                       ROUND(AVG(cpm), 1),
                       ROUND(AVG(accuracy) * 100, 1),
                       MAX(score),
                       MAX(max_combo)
                FROM game_results
            """).fetchone()
            if row and row[0] > 0:
                return [
                    ("总练习次数", str(row[0])),
                    ("平均 CPM", str(row[1])),
                    ("平均正确率", f"{row[2]}%"),
                    ("最高积分", str(row[3])),
                    ("最高连击", str(row[4])),
                ]
        except Exception:
            pass
        return [
            ("总练习次数", "0"),
            ("平均 CPM", "-"),
            ("平均正确率", "-"),
            ("最高积分", "-"),
            ("最高连击", "-"),
        ]

    def _load_history(self):
        db = App.instance().db
        try:
            rows = db.conn.execute("""
                SELECT played_at, mode, cpm, accuracy, score, max_combo, material_title
                FROM game_results
                ORDER BY played_at DESC
                LIMIT 50
            """).fetchall()
            self._table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                self._table.setItem(i, 0, QTableWidgetItem(str(row[0])[:16]))
                mode_names = {"follow": "跟打", "falling": "掉落", "timed": "限时"}
                self._table.setItem(i, 1, QTableWidgetItem(mode_names.get(row[1], row[1])))
                self._table.setItem(i, 2, QTableWidgetItem(f"{row[2]:.1f}"))
                self._table.setItem(i, 3, QTableWidgetItem(f"{row[3]:.0%}"))
                self._table.setItem(i, 4, QTableWidgetItem(str(row[4])))
                self._table.setItem(i, 5, QTableWidgetItem(str(row[5])))
                self._table.setItem(i, 6, QTableWidgetItem(str(row[6])))
        except Exception:
            self._table.setRowCount(0)

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有历史记录吗？\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db = App.instance().db
            db.conn.execute("DELETE FROM game_results")
            db.conn.commit()
            # Destroy the entire current widget and rebuild fresh
            old_layout = self.layout()
            if old_layout:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    w = item.widget()
                    if w:
                        w.deleteLater()
            self._build_ui()
