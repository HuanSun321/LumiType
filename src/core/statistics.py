import time
from collections import deque
from src.constants import CPM_WINDOW_SECONDS


class StatsCalculator:
    @staticmethod
    def cpm(correct_chars: int, elapsed_seconds: float) -> float:
        if elapsed_seconds <= 0:
            return 0.0
        return correct_chars / (elapsed_seconds / 60.0)

    @staticmethod
    def accuracy(correct: int, total: int) -> float:
        if total <= 0:
            return 1.0
        return correct / total

    @staticmethod
    def rolling_cpm(
        recent_chars: deque[tuple[float, bool]],
        window_seconds: float = CPM_WINDOW_SECONDS,
    ) -> float:
        if not recent_chars:
            return 0.0
        now = time.time()
        cutoff = now - window_seconds
        recent = [(t, ok) for t, ok in recent_chars if t >= cutoff]
        if not recent:
            return 0.0
        correct = sum(1 for _, ok in recent if ok)
        span = max(recent[-1][0] - recent[0][0], 1.0)
        return correct / (span / 60.0)
