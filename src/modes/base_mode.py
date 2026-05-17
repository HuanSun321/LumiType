import time
import random
from collections import deque
from src.core.statistics import StatsCalculator
from src.materials.material_manager import MaterialManager


class BaseTypingMode:
    """Shared logic for all typing modes."""

    def __init__(self):
        self._correct = 0
        self._wrong = 0
        self._total_typed = 0
        self._recent_chars: deque[tuple[float, bool]] = deque(maxlen=500)
        self._engine = None
        self._start_time = 0.0

    def setup(self, engine):
        self._engine = engine
        self._start_time = time.time()

    def teardown(self):
        pass

    def on_tick(self):
        pass

    def on_logic(self):
        pass

    @property
    def current_cpm(self) -> float:
        return StatsCalculator.rolling_cpm(self._recent_chars)

    @property
    def current_accuracy(self) -> float:
        return StatsCalculator.accuracy(self._correct, self._total_typed) if self._total_typed > 0 else 1.0

    def _record_char(self, is_correct: bool):
        self._total_typed += 1
        self._recent_chars.append((time.time(), is_correct))
        if is_correct:
            self._correct += 1
            if self._engine:
                self._engine.scoring.on_correct()
        else:
            self._wrong += 1
            if self._engine:
                self._engine.scoring.on_wrong()

    def _base_result(self, mode: str, material_title: str = "") -> dict:
        elapsed = max(time.time() - self._start_time, 0.001)
        return {
            "mode": mode,
            "total_chars": self._total_typed,
            "correct_chars": self._correct,
            "accuracy": StatsCalculator.accuracy(self._correct, self._total_typed),
            "cpm": StatsCalculator.cpm(self._correct, elapsed),
            "elapsed": elapsed,
            "material_title": material_title,
        }

    @staticmethod
    def load_idiom_batch(mm=None, batch_size: int = 15) -> tuple[dict, str]:
        """Load multiple idioms joined by comma. Shared across modes."""
        if mm is None:
            mm = MaterialManager.instance()
        all_m = [m for m in mm.get_materials(category="idiom") if len(m.get("content", "")) >= 2]
        if not all_m:
            m = mm.get_random_material(category="idiom")
            return m, m.get("content", "")
        batch = random.sample(all_m, min(batch_size, len(all_m)))
        text = "，".join(m.get("content", "") for m in batch)
        return {"title": "成语练习", "category": "idiom", "author": "", "content": text}, text
