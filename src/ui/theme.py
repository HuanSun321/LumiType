from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication
from src.constants import (
    COLOR_BG_PRIMARY, COLOR_BG_SECONDARY, COLOR_BG_CARD,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING, COLOR_HIGHLIGHT,
    COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT, COLOR_CREAM,
    COLOR_SKY, COLOR_PEACH,
    CJK_FONT_PREFERENCES, DEFAULT_FONT_SIZE,
)


class ThemeManager:
    CUTE_PALETTE = {
        "bg_primary": COLOR_BG_PRIMARY,
        "bg_secondary": COLOR_BG_SECONDARY,
        "bg_card": COLOR_BG_CARD,
        "text_primary": COLOR_TEXT_PRIMARY,
        "text_secondary": COLOR_TEXT_SECONDARY,
        "accent": COLOR_ACCENT,
        "success": COLOR_SUCCESS,
        "error": COLOR_ERROR,
        "warning": COLOR_WARNING,
        "highlight": COLOR_HIGHLIGHT,
        "pink_light": COLOR_PINK_LIGHT,
        "lavender": COLOR_LAVENDER,
        "mint": COLOR_MINT,
        "cream": COLOR_CREAM,
        "sky": COLOR_SKY,
        "peach": COLOR_PEACH,
    }

    def __init__(self, theme: str = "cute"):
        self._theme = theme
        self._font_family = self._detect_cjk_font()

    def _detect_cjk_font(self) -> str:
        available = QFontDatabase.families()
        for name in CJK_FONT_PREFERENCES:
            if name in available:
                return name
        return available[0] if available else "sans-serif"

    @property
    def font_family(self) -> str:
        return self._font_family

    @property
    def theme(self) -> str:
        return self._theme

    def set_theme(self, theme: str):
        self._theme = theme

    def get_font(self, size: int = DEFAULT_FONT_SIZE, bold: bool = False) -> QFont:
        font = QFont(self._font_family, size)
        font.setBold(bold)
        return font

    @property
    def palette(self) -> dict:
        return self.CUTE_PALETTE

    def get_stylesheet(self) -> str:
        p = self.palette
        return f"""
            QMainWindow, QWidget {{
                color: {p['text_primary']};
                font-family: "{self._font_family}";
            }}
            QMainWindow {{
                background: transparent;
            }}
            QStackedWidget {{
                background-color: {p['bg_primary']};
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }}
            QWidget#windowShell {{
                background-color: {p['bg_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 18px;
            }}
            QFrame#card {{
                background-color: {p['bg_card']};
                border: 2px dashed {p['pink_light']};
                border-radius: 18px;
                padding: 20px;
            }}
            QFrame#card:hover {{
                border: 2px dashed {p['accent']};
                background-color: {p['cream']};
            }}
            QPushButton {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 16px;
                padding: 10px 24px;
                font-size: 15px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background-color: {p['accent']};
                color: #ffffff;
                border-color: {p['accent']};
            }}
            QPushButton:focus {{
                border: 2px dashed {p['accent']};
            }}
            QPushButton:pressed {{
                background-color: #ff7096;
            }}
            QPushButton#primary {{
                background-color: {p['accent']};
                color: #ffffff;
                font-size: 18px;
                padding: 12px 32px;
                border: 2px solid {p['accent']};
                border-radius: 20px;
            }}
            QPushButton#primary:hover {{
                background-color: #ff7096;
                border-color: #ff7096;
            }}
            QPushButton#back_btn {{
                background-color: {p['lavender']};
                color: {p['text_primary']};
                border: 2px solid #d4b8e8;
                border-radius: 14px;
                padding: 8px 18px;
                font-size: 14px;
            }}
            QPushButton#back_btn:hover {{
                background-color: #d4b8e8;
            }}
            QLineEdit {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 16px;
                padding: 12px 16px;
                font-size: 20px;
                selection-background-color: {p['accent']};
            }}
            QLineEdit:focus {{
                border-color: {p['accent']};
                border-style: dashed;
            }}
            QLabel#title {{
                font-size: 36px;
                font-weight: bold;
                color: {p['accent']};
            }}
            QLabel#subtitle {{
                font-size: 18px;
                color: {p['text_secondary']};
            }}
            QLabel#stat_value {{
                font-size: 32px;
                font-weight: bold;
                color: {p['highlight']};
            }}
            QLabel#stat_label {{
                font-size: 14px;
                color: {p['text_secondary']};
            }}
            QComboBox {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 14px;
                min-height: 24px;
            }}
            QComboBox:hover, QSpinBox:hover, QLineEdit:hover {{
                border-color: {p['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 8px;
                padding: 4px;
                selection-background-color: {p['accent']};
                selection-color: #ffffff;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 4px 8px;
                min-height: 24px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {p['cream']};
            }}
            QAbstractItemView, QListView {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                selection-background-color: {p['accent']};
                selection-color: #ffffff;
                outline: none;
            }}
            QAbstractItemView::item, QListView::item {{
                min-height: 28px;
                padding: 6px 10px;
            }}
            QAbstractItemView::item:hover, QListView::item:hover {{
                background-color: {p['cream']};
                color: {p['text_primary']};
            }}
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                background: {p['pink_light']};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {p['accent']};
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
                border: 2px solid #ffffff;
            }}
            QSpinBox {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 10px;
                padding: 4px 8px;
                min-height: 28px;
            }}
            QCheckBox {{
                color: {p['text_primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid {p['pink_light']};
                background-color: {p['bg_card']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {p['accent']};
                border-color: {p['accent']};
            }}
            QProgressBar {{
                background-color: {p['pink_light']};
                border-radius: 6px;
                height: 10px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {p['accent']};
                border-radius: 6px;
            }}
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {p['accent']};
                border: 2px dashed {p['pink_light']};
                border-radius: 18px;
                margin-top: 12px;
                padding-top: 20px;
                background-color: rgba(255, 255, 255, 120);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
            }}
            QScrollBar:vertical {{
                background: {p['bg_secondary']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {p['pink_light']};
                min-height: 30px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {p['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QTableWidget {{
                background-color: {p['bg_card']};
                alternate-background-color: {p['bg_secondary']};
                color: {p['text_primary']};
                gridline-color: {p['pink_light']};
                border: 2px solid {p['pink_light']};
                border-radius: 12px;
            }}
            QHeaderView::section {{
                background-color: {p['lavender']};
                color: {p['text_primary']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {p['pink_light']};
                font-weight: bold;
            }}
            QListWidget {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: 2px solid {p['pink_light']};
                border-radius: 16px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px dashed {p['pink_light']};
                border-radius: 8px;
            }}
            QListWidget::item:hover {{
                background-color: {p['cream']};
            }}
            QListWidget::item:selected {{
                background-color: {p['accent']};
                color: #ffffff;
            }}
            QMessageBox {{
                background-color: {p['bg_primary']};
            }}
            QMessageBox QPushButton {{
                min-width: 80px;
            }}
        """
