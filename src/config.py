from PyQt6.QtCore import QSettings
from src.constants import (
    DEFAULT_DIFFICULTY, DEFAULT_FALLING_SPEED, DEFAULT_TIMED_DURATION,
    DEFAULT_FONT_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT,
)


class ConfigManager:
    DEFAULTS = {
        "difficulty": DEFAULT_DIFFICULTY,
        "falling_speed": DEFAULT_FALLING_SPEED,
        "timed_duration": DEFAULT_TIMED_DURATION,
        "material_source": "all",
        "font_family": "",
        "font_size": DEFAULT_FONT_SIZE,
        "sound_enabled": True,
        "sound_volume": 0.5,
        "theme": "cute",
        "window_width": WINDOW_WIDTH,
        "window_height": WINDOW_HEIGHT,
        "fullscreen_mode": True,
        "auto_update_materials": True,
        "falling_deco": "random",
        "content_ratio": 100,
        "show_keyboard_rabbit": True,
    }

    def __init__(self):
        self._settings = QSettings("逐字拾光", "逐字拾光")

    def get(self, key: str):
        default = self.DEFAULTS.get(key)
        value = self._settings.value(key, default)
        if value is None:
            return default
        if isinstance(default, bool):
            if isinstance(value, str):
                value = value.lower() == "true"
        elif isinstance(default, int):
            value = int(value)
        elif isinstance(default, float):
            value = float(value)
        return value

    def set(self, key: str, value):
        self._settings.setValue(key, value)

    def reset(self, key: str):
        self._settings.remove(key)
