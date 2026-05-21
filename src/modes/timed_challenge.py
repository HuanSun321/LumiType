"""Timed challenge mode: type as much as possible within a time limit."""
from src.core.game_state import GameMode
from src.constants import DEFAULT_TIMED_DURATION
from src.materials.material_manager import MaterialManager
from src.modes.base_mode import BaseSequentialTypingMode


class TimedChallengeMode(BaseSequentialTypingMode):
    mode = GameMode.TIMED_CHALLENGE

    def __init__(self, duration: int = DEFAULT_TIMED_DURATION, difficulty: int = 3,
                 category: str = None, ratio: float = 1.0):
        super().__init__()
        self._time_limit: int = duration
        self._time_remaining: float = 0.0
        self._difficulty = difficulty
        self._category = category
        self._ratio = ratio
        self._mm = MaterialManager.instance()
        self._completed_texts = 0
        self._material: dict = {}
        self._next_material: dict = {}
        self._load_next_text()

    @property
    def time_remaining(self) -> float:
        return max(0, self._time_remaining)

    @time_remaining.setter
    def time_remaining(self, value: float):
        self._time_remaining = value

    @property
    def duration(self) -> int:
        return self._time_limit

    @property
    def material(self) -> dict:
        return self._material

    @property
    def next_material(self) -> dict:
        return self._next_material

    @property
    def current_text(self) -> str:
        return self._text

    @property
    def completed_texts(self) -> int:
        return self._completed_texts

    def start(self):
        self.set_text(self._text)
        self._current_index = 0
        self._correct_count = 0
        self._total_typed = 0
        self._current_pinyin = ""
        self._time_remaining = float(self._time_limit)

    def process_input(self, typed: str) -> dict:
        result = super().process_input(typed)
        if self._current_index >= len(self._text) and self._text:
            self._completed_texts += 1
            self._load_next_text()
        return result

    def on_tick(self, dt: float = 0.016):
        if self._time_remaining > 0:
            self._time_remaining -= dt

    def on_logic(self):
        if self.is_game_over() and self._engine:
            self._engine.end()

    def is_game_over(self) -> bool:
        return self._time_remaining <= 0

    def get_result(self) -> dict:
        result = self._base_result("timed", f"限时挑战 ({self._time_limit}s)")
        result["completed_texts"] = self._completed_texts
        result["time_limit"] = self._time_limit
        return result

    def _load_next_text(self):
        category = self._category or ("poetry" if self._difficulty <= 4 else None)
        if self._category == "idiom":
            self._material, text = self.load_idiom_batch(self._mm, batch_size=10)
        else:
            self._material = self._next_material or self._mm.get_random_material(category=category)
            text = self._material.get("content", "")
        if self._ratio < 1.0 and text and self._category in ("article", "news"):
            text = text[:max(1, int(len(text) * self._ratio))]
        self.set_text(text.strip())
        if self._category == "idiom":
            self._next_material, _ = self.load_idiom_batch(self._mm, batch_size=10)
        else:
            self._next_material = self._mm.get_random_material(category=category)
