import time
from src.core.statistics import StatsCalculator
from src.materials.material_manager import MaterialManager
from src.modes.base_mode import BaseTypingMode


class FollowTypingMode(BaseTypingMode):
    def __init__(self, category: str = None, ratio: float = 1.0):
        super().__init__()
        mm = MaterialManager.instance()
        if category == "idiom":
            self._material, self._text = self.load_idiom_batch(mm)
        else:
            self._material = mm.get_random_material(category=category)
            self._text = self._material.get("content", "")
        if ratio < 1.0 and self._text and category in ("article", "news"):
            cut = max(1, int(len(self._text) * ratio))
            self._text = self._text[:cut]

        # Guard: strip leading/trailing whitespace and newlines
        self._text = self._text.strip()

        self._cursor = 0
        self._char_states: list[int] = []
        self._init_states()

    def _init_states(self):
        self._char_states = [0] * len(self._text)
        if self._char_states:
            self._char_states[0] = 3  # CURRENT

    @property
    def material(self) -> dict:
        return self._material

    @property
    def cursor_position(self) -> int:
        return self._cursor

    @property
    def char_states(self) -> list[int]:
        return list(self._char_states)

    def process_input(self, text: str):
        if self._cursor >= len(self._text) or not text:
            return

        for ch in text:
            if self._cursor >= len(self._text):
                break

            expected = self._text[self._cursor]
            is_correct = ch == expected
            self._record_char(is_correct)
            self._char_states[self._cursor] = 1 if is_correct else 2

            self._cursor += 1
            if self._cursor < len(self._text):
                self._char_states[self._cursor] = 3  # CURRENT

        if self._cursor >= len(self._text):
            if self._engine:
                self._engine.end()

    def calculate_result(self) -> dict:
        return self._base_result("follow", self._material.get("title", ""))
