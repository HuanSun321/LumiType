from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QApplication

from src.config import ConfigManager
from src.core.sound_manager import SoundManager
from src.db.database import DatabaseManager

if TYPE_CHECKING:
    pass


class App:
    """Application singleton holding shared resources."""

    _instance: App | None = None

    @classmethod
    def instance(cls) -> App:
        if cls._instance is None:
            raise RuntimeError("App not initialized. Call App(app) first.")
        return cls._instance

    def __init__(self, app: QApplication) -> None:
        if App._instance is not None:
            raise RuntimeError("App already initialized")
        App._instance = self

        self._qapp: QApplication = app
        self._config: ConfigManager = ConfigManager.instance()
        self._db: DatabaseManager = DatabaseManager.instance()
        self._sound: SoundManager = SoundManager.instance()

    @property
    def config(self) -> ConfigManager:
        return self._config

    @property
    def db(self) -> DatabaseManager:
        return self._db

    @property
    def sound(self) -> SoundManager:
        return self._sound

    def show(self) -> None:
        from src.ui.main_window import MainWindow
        self._window = MainWindow()
        self._window.show()

    def close(self) -> None:
        self._sound._cleanup_temp_dir()
        self._db.close()
