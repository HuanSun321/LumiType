from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QFont
from src.constants import COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_CREAM, COLOR_TEXT_PRIMARY


class TitleBar(QWidget):
    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_PINK_LIGHT};
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
            }}
        """)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 6, 0)
        layout.setSpacing(0)

        # Icon label
        self._icon_label = QLabel("雅")
        self._icon_label.setFixedSize(28, 28)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet(f"""
            background-color: {COLOR_ACCENT};
            color: white;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
            padding: 0;
        """)
        layout.addWidget(self._icon_label)

        # Title
        self._title_label = QLabel("  逐字拾光")
        self._title_label.setStyleSheet(f"""
            color: {COLOR_TEXT_PRIMARY};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(self._title_label)
        layout.addStretch()

        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 2px 8px;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.4);
            }}
        """
        close_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                padding: 2px 8px;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background-color: #FF6B8A;
                color: white;
            }}
        """

        self._min_btn = QPushButton("─")
        self._min_btn.setFixedSize(32, 28)
        self._min_btn.setStyleSheet(btn_style)
        self._min_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self._min_btn)

        self._max_btn = QPushButton("□")
        self._max_btn.setFixedSize(32, 28)
        self._max_btn.setStyleSheet(btn_style)
        self._max_btn.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(self._max_btn)

        self._close_btn = QPushButton("✕")
        self._close_btn.setFixedSize(32, 28)
        self._close_btn.setStyleSheet(close_style)
        self._close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self._close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self.maximize_clicked.emit()
