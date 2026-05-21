from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QSize, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QPainterPath, QRegion
from src.constants import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    COLOR_ACCENT, COLOR_PINK_LIGHT,
)
from src.ui.theme import ThemeManager
from src.ui.widgets.title_bar import TitleBar
from src.app import App


import os


def _create_app_icon() -> QIcon:
    """Load the app icon from 图标.png, fallback to generated 雅 icon."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icon_path = os.path.join(base, "图标.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    ico_path = os.path.join(base, "app.ico")
    if os.path.exists(ico_path):
        return QIcon(ico_path)
    # Fallback: generate pink-background 雅 icon
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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Apply saved window state
        config = App.instance().config
        fullscreen = config.get("fullscreen_mode")
        if fullscreen:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            if screen:
                self.showFullScreen()
                self.setGeometry(screen.availableGeometry())
            else:
                self.show()
            self._is_fullscreen = True
        else:
            w = config.get("window_width")
            h = config.get("window_height")
            self.resize(w, h)
            self.show()
            self._is_fullscreen = False

        self._is_maximized = False
        self._normal_geometry = None  # saved geometry before maximize

        self._theme = ThemeManager()
        App.instance()._qapp.setStyleSheet(self._theme.get_stylesheet())

        # Build UI
        central = QWidget()
        central.setObjectName("windowShell")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._title_bar = TitleBar()
        self._title_bar.close_clicked.connect(self.close)
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.maximize_clicked.connect(self._toggle_maximize)
        self._title_bar.set_fullscreen_mode(self._is_fullscreen)
        main_layout.addWidget(self._title_bar)

        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # The visible shell owns the rounded background; QMainWindow stays transparent
        # so desktop pixels show through the four corners.
        central.setStyleSheet(f"""
            QWidget#windowShell {{
                background-color: #FFF5F5;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 18px;
            }}
        """)

        self._screens = {}
        self._init_screens()
        self._sync_window_shape()

    def _toggle_maximize(self):
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()

        if self._is_fullscreen:
            # Exit fullscreen → back to normal windowed
            config = App.instance().config
            w = config.get("window_width")
            h = config.get("window_height")
            self.showNormal()
            self.setGeometry(0, 0, w, h)
            self.move(geo.center() - self.rect().center())
            self._is_fullscreen = False
            App.instance().config.set("fullscreen_mode", False)
            self._title_bar.set_fullscreen_mode(False)
            self._sync_window_shape()
        elif self._is_maximized:
            # Restore to saved geometry
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self._is_maximized = False
            self._sync_window_shape()
        else:
            # Maximize: save current geometry, then fill screen
            self._normal_geometry = self.geometry()
            self.setGeometry(geo)
            self._is_maximized = True
            self._sync_window_shape()

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
        self._is_fullscreen = fullscreen
        if fullscreen:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            if screen:
                self._is_maximized = False
                self.showFullScreen()
                self.setGeometry(screen.availableGeometry())
            self._title_bar.set_fullscreen_mode(True)
            self._sync_window_shape()
        elif width and height:
            config.set("window_width", width)
            config.set("window_height", height)
            self._is_maximized = False
            self.showNormal()
            self.resize(width, height)
            self._title_bar.set_fullscreen_mode(False)
            self._sync_window_shape()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_window_shape()

    def _sync_window_shape(self):
        shell = self.centralWidget()
        if not shell:
            return
        if self._is_fullscreen or self._is_maximized:
            self.clearMask()
            shell.setStyleSheet(f"""
                QWidget#windowShell {{
                    background-color: #FFF5F5;
                    border: none;
                    border-radius: 0px;
                }}
            """)
            return

        radius = 18
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path.addRoundedRect(rect, radius, radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        shell.setStyleSheet(f"""
            QWidget#windowShell {{
                background-color: #FFF5F5;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: {radius}px;
            }}
        """)

    @property
    def theme(self) -> ThemeManager:
        return self._theme
