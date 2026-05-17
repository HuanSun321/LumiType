import time
import random
from src.core.statistics import StatsCalculator
from src.materials.material_manager import MaterialManager
from src.modes.base_mode import BaseTypingMode


class TimedChallengeMode(BaseTypingMode):
    """Type as many short texts as possible within a time limit. Combo scoring."""

    def __init__(self, duration: int = 120, difficulty: int = 3, category: str = None, ratio: float = 1.0):
        super().__init__()
        self._duration = duration
        self._difficulty = difficulty
        self._category = category
        self._ratio = ratio
        self._mm = MaterialManager.instance()

        self._completed_texts = 0

        # Current text
        self._current_material: dict = {}
        self._current_text: str = ""
        self._cursor: int = 0
        self._char_states: list[int] = []
        self._next_material: dict = {}

        self._load_next_text()

    def _load_next_text(self):
        category = self._category or ("poetry" if self._difficulty <= 4 else None)

        if self._category == "idiom":
            self._current_material, self._current_text = self.load_idiom_batch(self._mm, batch_size=10)
        else:
            self._current_material = self._next_material or self._mm.get_random_material(category=category)
            self._current_text = self._current_material.get("content", "")
        self._cursor = 0
        self._char_states = [0] * len(self._current_text)
        if self._char_states:
            self._char_states[0] = 3  # CURRENT

        # Pre-load next
        if self._category == "idiom":
            self._next_material, _ = self.load_idiom_batch(self._mm, batch_size=10)
        else:
            self._next_material = self._mm.get_random_material(category=category)

    @property
    def material(self) -> dict:
        return self._current_material

    @property
    def next_material(self) -> dict:
        return self._next_material

    @property
    def cursor_position(self) -> int:
        return self._cursor

    @property
    def char_states(self) -> list[int]:
        return list(self._char_states)

    @property
    def current_text(self) -> str:
        return self._current_text

    @property
    def time_remaining(self) -> int:
        if not self._start_time:
            return self._duration
        elapsed = time.time() - self._start_time
        return max(0, int(self._duration - elapsed))

    @property
    def completed_texts(self) -> int:
        return self._completed_texts

    @property
    def duration(self) -> int:
        return self._duration

    def process_input(self, text: str):
        if self.time_remaining <= 0 or not text:
            return

        for ch in text:
            if self._cursor >= len(self._current_text):
                break

            expected = self._current_text[self._cursor]
            is_correct = ch == expected
            self._record_char(is_correct)
            self._char_states[self._cursor] = 1 if is_correct else 2

            self._cursor += 1
            if self._cursor < len(self._current_text):
                self._char_states[self._cursor] = 3  # CURRENT

        # Check if current text is completed
        if self._cursor >= len(self._current_text):
            self._completed_texts += 1
            self._load_next_text()

    def on_logic(self):
        if self._start_time and self.time_remaining <= 0:
            if self._engine:
                self._engine.end()

    def calculate_result(self) -> dict:
        result = self._base_result("timed", f"限时挑战 ({self._duration}s)")
        result["completed_texts"] = self._completed_texts
        return result
