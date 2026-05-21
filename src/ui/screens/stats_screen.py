from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDateEdit, QFrame,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from src.app import App
from src.constants import (
    COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH, COLOR_SKY, COLOR_ERROR,
)


def _summary_card(label_text: str, value_text: str, emoji: str, bg: str,
                  change_text: str = "", change_positive: bool = True) -> QVBoxLayout:
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
    if change_text:
        change_color = "#8BD3A8" if change_positive else "#FF6B8A"
        change = QLabel(change_text)
        change.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {change_color};")
        change.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.addWidget(change)
    return card


class BarChartWidget(QWidget):
    """Hand-drawn style bar chart for daily practice statistics."""

    def __init__(self):
        super().__init__()
        self._data = []  # list of (label, value, color)
        self.setMinimumHeight(180)

    def set_data(self, data: list[tuple[str, float, str]]):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin_left = 50
        margin_right = 20
        margin_top = 20
        margin_bottom = 40

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        # Background
        painter.fillRect(self.rect(), QColor("#FFFAF5"))

        # Grid lines (hand-drawn dashed)
        painter.setPen(QPen(QColor("#E8DAEF"), 1, Qt.PenStyle.DashLine))
        max_val = max((v for _, v, _ in self._data), default=1)
        if max_val == 0:
            max_val = 1
        for i in range(5):
            y = margin_top + chart_h * (1 - i / 4)
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            label = str(int(max_val * i / 4))
            painter.setPen(QColor("#A08888"))
            painter.setFont(QFont("Microsoft YaHei", 9))
            painter.drawText(5, int(y - 6), 40, 14, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
            painter.setPen(QPen(QColor("#E8DAEF"), 1, Qt.PenStyle.DashLine))

        # Bars
        n = len(self._data)
        if n == 0:
            return
        bar_gap = 8
        bar_width = max(20, min(60, (chart_w - bar_gap * (n + 1)) / n))
        total_bars_w = bar_width * n + bar_gap * (n + 1)
        start_x = margin_left + (chart_w - total_bars_w) / 2

        for i, (label, value, color_hex) in enumerate(self._data):
            x = start_x + bar_gap + i * (bar_width + bar_gap)
            bar_h = (value / max_val) * chart_h if max_val > 0 else 0
            y = margin_top + chart_h - bar_h

            # Bar with rounded top (hand-drawn style)
            color = QColor(color_hex)
            painter.setPen(QPen(color.darker(120), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_h), 6, 6)

            # Value on top
            if value > 0:
                painter.setPen(QColor("#5B4A4A"))
                painter.setFont(QFont("Microsoft YaHei", 9, QFont.Weight.Bold))
                val_text = f"{value:.0f}" if value == int(value) else f"{value:.1f}"
                painter.drawText(int(x - 5), int(y - 18), int(bar_width + 10), 16,
                                 Qt.AlignmentFlag.AlignCenter, val_text)

            # Label below
            painter.setPen(QColor("#A08888"))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(int(x - 5), int(margin_top + chart_h + 4), int(bar_width + 10), 20,
                             Qt.AlignmentFlag.AlignCenter, label)

        painter.end()


class StatsScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()
        self._date_start = None
        self._date_end = None

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
        back_btn = QPushButton("返回")
        back_btn.setObjectName("back_btn")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.navigate_to("menu") if self.navigate_to else None)
        header.addWidget(back_btn)
        header.addStretch()
        title = QLabel("历史记录")
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLOR_ACCENT};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Date filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        filter_bar.addWidget(QLabel("从:"))
        self._date_start = QDateEdit()
        self._date_start.setCalendarPopup(True)
        self._date_start.setDate(QDate.currentDate().addMonths(-1))
        self._date_start.setFixedWidth(130)
        self._date_start.setStyleSheet(f"""
            QDateEdit {{
                background-color: {COLOR_CREAM};
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 8px;
                padding: 4px 8px;
            }}
        """)
        filter_bar.addWidget(self._date_start)

        filter_bar.addWidget(QLabel("至:"))
        self._date_end = QDateEdit()
        self._date_end.setCalendarPopup(True)
        self._date_end.setDate(QDate.currentDate())
        self._date_end.setFixedWidth(130)
        self._date_end.setStyleSheet(f"""
            QDateEdit {{
                background-color: {COLOR_CREAM};
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 8px;
                padding: 4px 8px;
            }}
        """)
        filter_bar.addWidget(self._date_end)

        filter_bar.addSpacing(8)

        quick_btns = [
            ("今天", 0), ("本周", 7), ("本月", 30), ("全部", -1),
        ]
        for text, days in quick_btns:
            btn = QPushButton(text)
            btn.setFixedWidth(60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_LAVENDER};
                    color: #5B4A4A;
                    border: 2px solid {COLOR_PINK_LIGHT};
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_ACCENT};
                    color: #ffffff;
                }}
            """)
            btn.clicked.connect(lambda checked, d=days: self._set_quick_date(d))
            filter_bar.addWidget(btn)

        filter_btn = QPushButton("筛选")
        filter_btn.setFixedWidth(60)
        filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: 2px solid {COLOR_ACCENT};
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #ff7096; }}
        """)
        filter_btn.clicked.connect(self._refresh_stats)
        filter_bar.addWidget(filter_btn)

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Summary stats with comparison
        self._summary_layout = QHBoxLayout()
        self._summary_layout.setSpacing(24)
        self._summary_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(self._summary_layout)

        # Bar chart
        self._chart = BarChartWidget()
        self._chart.setMinimumHeight(200)
        layout.addWidget(self._chart)

        self._mistake_panel = QLabel("")
        self._mistake_panel.setWordWrap(True)
        self._mistake_panel.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_CREAM};
                color: #5B4A4A;
                border: 2px dashed {COLOR_PINK_LIGHT};
                border-radius: 14px;
                padding: 10px 14px;
                font-size: 14px;
            }}
        """)
        layout.addWidget(self._mistake_panel)

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
        layout.addWidget(self._table)

        # Bottom bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        clear_btn = QPushButton("清空历史记录")
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

        self._refresh_stats()

    def _set_quick_date(self, days: int):
        today = QDate.currentDate()
        if days == 0:
            self._date_start.setDate(today)
        elif days == -1:
            self._date_start.setDate(QDate(2020, 1, 1))
        else:
            self._date_start.setDate(today.addDays(-days))
        self._date_end.setDate(today)
        self._refresh_stats()

    def _refresh_stats(self):
        start = self._date_start.date().toString("yyyy-MM-dd")
        end = self._date_end.date().addDays(1).toString("yyyy-MM-dd")
        period_days = self._date_start.date().daysTo(self._date_end.date()) + 1

        # Current period stats
        current = self._query_stats(start, end)

        # Previous period stats (same duration, ending at start)
        prev_end = start
        prev_start_dt = self._date_start.date().addDays(-period_days)
        prev_start = prev_start_dt.toString("yyyy-MM-dd")
        previous = self._query_stats(prev_start, prev_end)

        self._update_summary_cards(current, previous)
        self._update_chart(start, end)
        self._update_mistake_panel(start, end)
        self._load_history(start, end)

    def _query_stats(self, start: str, end: str) -> dict:
        db = App.instance().db
        return db.query_stats(start, end)

    def _format_change(self, current: float, previous: float, suffix: str = "%") -> tuple[str, bool]:
        """Format comparison text. Returns (text, is_positive)."""
        if previous == 0:
            if current > 0:
                return (f"+{current:.1f}{suffix}", True)
            return ("-", True)
        diff = current - previous
        pct = (diff / previous) * 100
        is_pos = diff >= 0
        sign = "+" if is_pos else ""
        return (f"{sign}{pct:.1f}%", is_pos)

    def _update_summary_cards(self, current: dict, previous: dict):
        # Clear old cards
        while self._summary_layout.count():
            item = self._summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        acc_cur = current["avg_accuracy"] * 100
        acc_prev = previous["avg_accuracy"] * 100

        cards = [
            ("练习次数", str(current["count"]), "📝", COLOR_LAVENDER,
             *self._format_change(current["count"], previous["count"], "")),
            ("平均 CPM", f"{current['avg_cpm']:.1f}", "⚡", COLOR_SKY,
             *self._format_change(current["avg_cpm"], previous["avg_cpm"])),
            ("平均正确率", f"{acc_cur:.1f}%", "🎯", COLOR_MINT,
             *self._format_change(acc_cur, acc_prev)),
            ("最高积分", str(current["max_score"]), "✨", COLOR_CREAM,
             *self._format_change(current["max_score"], previous["max_score"], "")),
            ("最高连击", str(current["max_combo"]), "🔥", COLOR_PEACH,
             *self._format_change(current["max_combo"], previous["max_combo"], "")),
        ]
        streak = App.instance().db.query_streak_days()
        top_mistakes = App.instance().db.query_top_mistakes(limit=1)
        cards.append(("连续天数", f"{streak} 天", "🌱", COLOR_MINT, "", True))
        cards.append(("常错字", top_mistakes[0]["expected"] if top_mistakes else "-", "🧭", COLOR_CREAM, "", True))
        for label, value, emoji, bg, change, is_pos in cards:
            self._summary_layout.addLayout(
                _summary_card(label, value, emoji, bg, change, is_pos)
            )

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _update_chart(self, start: str, end: str):
        """Update bar chart with daily practice counts for the last 7 days."""
        db = App.instance().db
        daily_data = db.query_daily_chart(start, end)

        colors = [
            "#FFD1DC", "#E8DAEF", "#D5F5E3", "#D6EAF8",
            "#FDEBD0", "#C5A3FF", "#FFB86C",
            "#FFD1DC", "#E8DAEF", "#D5F5E3", "#D6EAF8",
            "#FDEBD0", "#C5A3FF", "#FFB86C",
        ]
        data = []
        for i, (day_label, count, avg_cpm) in enumerate(daily_data):
            data.append((day_label, float(count), colors[i % len(colors)]))

        self._chart.set_data(data if data else [("无数据", 0, COLOR_LAVENDER)])

    def _update_mistake_panel(self, start: str, end: str):
        mistakes = App.instance().db.query_top_mistakes(limit=8, start=start, end=end)
        if not mistakes:
            self._mistake_panel.setText("常错字：暂无记录。完成一次练习后，这里会显示需要复训的字。")
            return
        parts = []
        for item in mistakes:
            actual = f" / 常误输 {item['last_actual']}" if item.get("last_actual") else ""
            parts.append(f"{item['expected']} ×{item['count']}{actual}")
        self._mistake_panel.setText("常错字：" + "  ".join(parts))

    def _load_history(self, start: str = None, end: str = None):
        db = App.instance().db
        try:
            if start and end:
                rows = db.conn.execute("""
                    SELECT played_at, mode, cpm, accuracy, score, max_combo, material_title
                    FROM game_results
                    WHERE played_at >= ? AND played_at < ?
                    ORDER BY played_at DESC
                    LIMIT 50
                """, (start, end)).fetchall()
            else:
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
            self._refresh_stats()
