from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen
from src.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    COLOR_ACCENT, COLOR_PINK_LIGHT,
)
from src.ui.theme import ThemeManager
from src.ui.widgets.title_bar import TitleBar
from src.app import App


def _create_app_icon() -> QIcon:
    """Generate a pink-background icon with 雅 character."""
    size = 128
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(COLOR_ACCENT))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    font = QFont("Microsoft YaHei", 72, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QPen(QColor("white")))
    painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, "雅")
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("逐字拾光")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Apply icon
        self.setWindowIcon(_create_app_icon())

        # Frameless window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Apply saved window state
        config = App.instance().config
        fullscreen = config.get("fullscreen_mode")
        if fullscreen:
            self.showFullScreen()
        else:
            w = config.get("window_width")
            h = config.get("window_height")
            self.resize(w, h)
            self.show()

        self._is_fullscreen = fullscreen

        self._theme = ThemeManager()

        # Build UI
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._title_bar = TitleBar()
        self._title_bar.close_clicked.connect(self.close)
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.maximize_clicked.connect(self._toggle_maximize)
        main_layout.addWidget(self._title_bar)

        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # Rounded window styling
        self.setStyleSheet(f"""
            QMainWindow {{
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 14px;
            }}
        """)

        self._screens = {}
        self._init_screens()

    def _toggle_maximize(self):
        if self.isFullScreen():
            config = App.instance().config
            w = config.get("window_width")
            h = config.get("window_height")
            self.resize(w, h)
            self.showNormal()
        elif self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _init_screens(self):
        from src.ui.screens.menu_screen import MenuScreen
        from src.ui.screens.game_screen import GameScreen
        from src.ui.screens.results_screen import ResultsScreen
        from src.ui.screens.settings_screen import SettingsScreen
        from src.ui.screens.stats_screen import StatsScreen
        from src.ui.screens.material_screen import MaterialScreen

        self._add_screen("menu", MenuScreen())
        self._add_screen("game", GameScreen())
        self._add_screen("results", ResultsScreen())
        self._add_screen("settings", SettingsScreen())
        self._add_screen("stats", StatsScreen())
        self._add_screen("material", MaterialScreen())

    def _add_screen(self, name: str, widget):
        self._screens[name] = widget
        self._stack.addWidget(widget)
        widget.navigate_to = self.navigate_to

    def navigate_to(self, name: str, data: dict | None = None):
        if name in self._screens:
            screen = self._screens[name]
            if hasattr(screen, "on_enter"):
                screen.on_enter(data or {})
            self._stack.setCurrentWidget(screen)

    def apply_display_mode(self, fullscreen: bool, width: int = 0, height: int = 0):
        """Called by settings screen to apply display mode changes."""
        config = App.instance().config
        config.set("fullscreen_mode", fullscreen)
        if not fullscreen and width and height:
            config.set("window_width", width)
            config.set("window_height", height)
            self.resize(width, height)
            self.showNormal()
        elif fullscreen:
            self.showFullScreen()

    @property
    def theme(self) -> ThemeManager:
        return self._theme
