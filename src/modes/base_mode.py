"""Base class for typing practice modes."""
import random
import time
from collections import deque

from src.core.game_state import GameMode
from src.core.statistics import StatsCalculator
from src.materials.material_manager import MaterialManager


class BaseTypingMode:
    """Abstract base for all game modes."""

    mode: GameMode = GameMode.FOLLOW_TYPING
    _text: str = ""

    def __init__(self):
        self._engine = None
        self._start_time = 0.0
        self._recent_chars: deque[tuple[float, bool]] = deque(maxlen=500)
        self._mistake_events: list[dict] = []
        self._correct_count = 0
        self._total_typed = 0
        self._current_pinyin = ""

    @property
    def text(self) -> str:
        return self._text

    def set_text(self, text: str):
        self._text = text

    def start(self):
        raise NotImplementedError

    def setup(self, engine):
        self._engine = engine
        self._start_time = time.time()
        self._recent_chars.clear()
        self._mistake_events.clear()
        self.start()

    def teardown(self):
        pass

    def process_input(self, typed: str) -> dict:
        raise NotImplementedError

    def on_tick(self, dt: float = 0.016):
        pass

    def on_logic(self):
        pass

    def get_result(self) -> dict:
        raise NotImplementedError

    def calculate_result(self) -> dict:
        return self.get_result()

    def is_game_over(self) -> bool:
        return False

    @property
    def current_pinyin(self) -> str:
        return self._current_pinyin

    @current_pinyin.setter
    def current_pinyin(self, value: str):
        self._current_pinyin = value

    def _record_char(self, is_correct: bool):
        self._total_typed += 1
        self._recent_chars.append((time.time(), is_correct))
        if is_correct:
            self._correct_count += 1
            if self._engine:
                self._engine.scoring.on_correct()
        elif self._engine:
            self._engine.scoring.on_wrong()

    @property
    def mistake_events(self) -> list[dict]:
        return list(self._mistake_events)

    def _record_mistake(self, expected: str, actual: str, position: int, context: str = ""):
        expected = expected or ""
        if not expected:
            return
        if not context and self._text:
            start = max(0, position - 4)
            end = min(len(self._text), position + 5)
            context = self._text[start:end]
        self._mistake_events.append({
            "expected": expected,
            "actual": actual or "",
            "position": position,
            "context": context,
        })

    @staticmethod
    def load_idiom_batch(mm=None, batch_size: int = 15) -> tuple[dict, str]:
        if mm is None:
            mm = MaterialManager.instance()
        all_m = [m for m in mm.get_materials(category="idiom") if len(m.get("content", "")) >= 2]
        if not all_m:
            m = mm.get_random_material(category="idiom")
            return m, m.get("content", "")
        batch = random.sample(all_m, min(batch_size, len(all_m)))
        text = "，".join(m.get("content", "") for m in batch)
        return {"title": "成语练习", "category": "idiom", "author": "", "content": text}, text


class BaseSequentialTypingMode(BaseTypingMode):
    """Base for modes where user types text sequentially (follow + timed).

    Provides shared logic for character-by-character comparison,
    accuracy tracking, and char state management.
    """

    def __init__(self):
        super().__init__()
        self._char_states: list[int] = []
        self._current_index: int = 0
        self._correct_count: int = 0
        self._total_typed: int = 0
        self._current_pinyin: str = ""

    def set_text(self, text: str):
        super().set_text(text)
        self._char_states = [0] * len(text)
        if self._char_states:
            self._char_states[0] = 3
        self._current_index = 0
        self._correct_count = 0
        self._total_typed = 0

    def process_input(self, typed: str) -> dict:
        """Compare typed text against target text character by character."""
        if not self._text:
            return {"correct": 0, "total": 0, "accuracy": 0.0, "finished": False}

        for ch in typed:
            if self._current_index >= len(self._text):
                break
            expected = self._text[self._current_index]
            is_correct = ch == expected
            self._record_char(is_correct)
            if not is_correct:
                self._record_mistake(expected, ch, self._current_index)
            self._char_states[self._current_index] = 1 if is_correct else 2
            self._current_index += 1
            if self._current_index < len(self._char_states):
                self._char_states[self._current_index] = 3

        accuracy = self.current_accuracy

        return {
            "correct": self._correct_count,
            "total": self._total_typed,
            "accuracy": accuracy,
            "finished": self.is_game_over(),
        }

    @property
    def char_states(self) -> list[int]:
        return list(self._char_states)

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def cursor_position(self) -> int:
        return self._current_index

    @property
    def current_cpm(self) -> float:
        rolling = StatsCalculator.rolling_cpm(self._recent_chars)
        if rolling:
            return rolling
        elapsed = max(time.time() - self._start_time, 0.001)
        return StatsCalculator.cpm(self._correct_count, elapsed)

    @property
    def current_accuracy(self) -> float:
        return StatsCalculator.accuracy(self._correct_count, self._total_typed)

    @property
    def current_pinyin(self) -> str:
        return self._current_pinyin

    @current_pinyin.setter
    def current_pinyin(self, value: str):
        self._current_pinyin = value

    def _update_preview(self):
        """Override in subclasses if preview update is needed."""
        pass

    def _record_char(self, is_correct: bool):
        self._total_typed += 1
        self._recent_chars.append((time.time(), is_correct))
        if is_correct:
            self._correct_count += 1
            if self._engine:
                self._engine.scoring.on_correct()
        elif self._engine:
            self._engine.scoring.on_wrong()

    def _base_result(self, mode: str, material_title: str = "") -> dict:
        elapsed = max(time.time() - self._start_time, 0.001)
        return {
            "mode": mode,
            "total_chars": self._total_typed,
            "correct_chars": self._correct_count,
            "accuracy": StatsCalculator.accuracy(self._correct_count, self._total_typed),
            "cpm": StatsCalculator.cpm(self._correct_count, elapsed),
            "elapsed": elapsed,
            "material_title": material_title,
        }
