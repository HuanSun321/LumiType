from src.config import ConfigManager
from src.db.database import DatabaseManager
from src.core.sound_manager import SoundManager


class App:
    _instance = None

    def __init__(self):
        if App._instance is not None:
            raise RuntimeError("Use App.instance()")
        App._instance = self
        self.config = ConfigManager()
        self.db = DatabaseManager()
        self.sound = SoundManager()
        self.sound.set_enabled(self.config.get("sound_enabled"))
        self._sound_volume = self.config.get("sound_volume")
        self.sound.set_volume(self._sound_volume)

    @classmethod
    def instance(cls):
        return cls._instance
