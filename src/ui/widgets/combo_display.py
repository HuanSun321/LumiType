from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QFont
from src.app import App
from src.constants import COLOR_ACCENT, COLOR_HIGHLIGHT, DEFAULT_FONT_SIZE


class ComboDisplay(QWidget):
    """Animated combo counter with cute style."""

    def __init__(self):
        super().__init__()
        self.setFixedHeight(44)
        self._combo = 0
        self._multiplier = 1.0

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        config = App.instance().config
        font_family = config.get("font_family") or "Microsoft YaHei"
        font_size = config.get("font_size") or DEFAULT_FONT_SIZE

        self._label = QLabel("")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont(font_family, max(14, font_size - 6), QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {COLOR_HIGHLIGHT};")
        layout.addWidget(self._label)

        self._opacity_effect = QGraphicsOpacityEffect(self._label)
        self._label.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(1000)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self._on_fade_done)

        self._hide_timer = None

    def show_combo(self, combo: int, multiplier: float):
        self._fade_anim.stop()
        self._opacity_effect.setOpacity(1.0)
        self._combo = combo
        self._multiplier = multiplier
        self._label.setText(f"🌟 {combo} 连击! ×{multiplier:.1f} 🌟")
        self._label.setStyleSheet(f"""
            color: {COLOR_HIGHLIGHT};
            font-size: 20px;
            font-weight: bold;
            background-color: #FFF8E7;
            border: 2px dashed #FFD700;
            border-radius: 14px;
            padding: 4px 16px;
        """)
        if self._hide_timer is None:
            from PyQt6.QtCore import QTimer
            self._hide_timer = QTimer(self)
            self._hide_timer.setSingleShot(True)
            self._hide_timer.setInterval(2000)
            self._hide_timer.timeout.connect(self._fade_anim.start)
        self._hide_timer.start()

    def _on_fade_done(self):
        self._label.setText("")
        self._label.setStyleSheet(f"color: {COLOR_HIGHLIGHT};")
        self._opacity_effect.setOpacity(1.0)
