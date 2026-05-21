"""Follow-typing mode: user types the displayed text sequentially."""
from src.core.game_state import GameMode
from src.materials.material_manager import MaterialManager
from src.modes.base_mode import BaseSequentialTypingMode


class FollowTypingMode(BaseSequentialTypingMode):
    mode = GameMode.FOLLOW_TYPING

    def __init__(self, category: str = None, ratio: float = 1.0, material: dict | None = None):
        super().__init__()
        if material:
            self._material = dict(material)
            text = self._material.get("content", "")
        else:
            mm = MaterialManager.instance()
            if category == "idiom":
                self._material, text = self.load_idiom_batch(mm)
            else:
                self._material = mm.get_random_material(category=category)
                text = self._material.get("content", "")
        if ratio < 1.0 and text and (category or self._material.get("category")) in ("article", "news"):
            text = text[:max(1, int(len(text) * ratio))]
        self.set_text(text.strip())

    def start(self):
        self.set_text(self._text)
        self._current_index = 0
        self._correct_count = 0
        self._total_typed = 0
        self._current_pinyin = ""

    @property
    def material(self) -> dict:
        return self._material

    def get_result(self) -> dict:
        return self._base_result("follow", self._material.get("title", ""))

    def is_game_over(self) -> bool:
        return self._current_index >= len(self._text)
