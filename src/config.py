import logging
from PyQt6.QtCore import QSettings
from src.constants import DEFAULT_DIFFICULTY, DEFAULT_FALLING_SPEED, DEFAULT_FONT_SIZE, DEFAULT_TIMED_DURATION, WINDOW_HEIGHT, WINDOW_WIDTH


# Valid ranges for config values
_CONFIG_VALIDATORS = {
    "difficulty": lambda v: isinstance(v, int) and 1 <= v <= 5,
    "falling_speed": lambda v: isinstance(v, int) and 1 <= v <= 5,
    "timed_duration": lambda v: isinstance(v, int) and v > 0,
    "content_ratio": lambda v: isinstance(v, int) and 1 <= v <= 100,
    "font_size": lambda v: isinstance(v, int) and 12 <= v <= 72,
    "sound_volume": lambda v: isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0,
    "sound_enabled": lambda v: isinstance(v, bool),
    "show_keyboard_rabbit": lambda v: isinstance(v, bool),
    "keyboard_rabbit_scale": lambda v: isinstance(v, int) and 60 <= v <= 140,
    "fullscreen_mode": lambda v: isinstance(v, bool),
    "auto_update_materials": lambda v: isinstance(v, bool),
    "theme": lambda v: isinstance(v, str) and v in ("light", "dark", "auto"),
}


class ConfigManager:
    """Application configuration manager with value validation."""

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._settings = QSettings("逐字拾光", "逐字拾光")
        self._defaults = {
            "difficulty": DEFAULT_DIFFICULTY,
            "falling_speed": DEFAULT_FALLING_SPEED,
            "timed_duration": DEFAULT_TIMED_DURATION,
            "content_ratio": 100,
            "falling_deco": "random",
            "font_family": "Microsoft YaHei",
            "font_size": DEFAULT_FONT_SIZE,
            "sound_enabled": True,
            "sound_volume": 0.7,
            "auto_update_materials": True,
            "show_keyboard_rabbit": True,
            "keyboard_rabbit_scale": 80,
            "fullscreen_mode": False,
            "window_width": WINDOW_WIDTH,
            "window_height": WINDOW_HEIGHT,
            "theme": "light",
        }

    def get(self, key: str, default=None):
        value = self._settings.value(key, default if default is not None else self._defaults.get(key))
        # Type conversion for known keys
        if key in ("difficulty", "falling_speed", "timed_duration", "content_ratio", "font_size",
                   "keyboard_rabbit_scale", "window_width", "window_height") and isinstance(value, str):
            try:
                value = int(value)
            except (ValueError, TypeError):
                value = self._defaults.get(key)
        elif key in ("sound_volume",) and isinstance(value, str):
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = self._defaults.get(key, 0.7)
        elif key in ("auto_update_materials", "sound_enabled", "show_keyboard_rabbit",
                     "fullscreen_mode") and isinstance(value, str):
            value = value.lower() in ("true", "1", "yes")
        if value is None:
            value = self._defaults.get(key, default)
        return value

    def set(self, key: str, value):
        """Set a config value with validation. Logs warning and ignores invalid values."""
        validator = _CONFIG_VALIDATORS.get(key)
        if validator and not validator(value):
            logging.warning("ConfigManager: invalid value for '%s': %r (ignored)", key, value)
            return
        self._settings.setValue(key, value)
