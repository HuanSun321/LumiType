from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from src.constants import COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_CREAM, COLOR_TEXT_PRIMARY
import os


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
        self._fullscreen = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 6, 0)
        layout.setSpacing(0)

        # Icon label — use 图标.png if available, else fallback to 雅 text
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "图标.png",
        )
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(28, 28)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(
                28, 28, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._icon_label.setPixmap(pix)
            self._icon_label.setStyleSheet("background: transparent; border-radius: 6px; padding: 0;")
        else:
            self._icon_label.setText("雅")
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

    def set_fullscreen_mode(self, fullscreen: bool):
        """Hide min/max buttons and disable drag in fullscreen."""
        self._fullscreen = fullscreen
        self._min_btn.setVisible(not fullscreen)
        self._max_btn.setVisible(not fullscreen)

    def mousePressEvent(self, event):
        if self._fullscreen:
            event.ignore()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._fullscreen:
            event.ignore()
            return
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._fullscreen = False

    def mouseDoubleClickEvent(self, event):
        if self._fullscreen:
            event.ignore()
            return
        self.maximize_clicked.emit()
