"""Scoring engine for typing practice."""
from src.constants import BASE_POINTS_PER_CHAR, MAX_COMBO_MULTIPLIER, COMBO_STEP


class ScoringEngine:
    """Calculates score, combo, and CPM for typing practice."""

    def __init__(self) -> None:
        self._score: int = 0
        self._combo: int = 0
        self._max_combo: int = 0

    @property
    def score(self) -> int:
        return self._score

    @property
    def combo(self) -> int:
        return self._combo

    @property
    def max_combo(self) -> int:
        return self._max_combo

    def combo_multiplier(self) -> float:
        """Return current combo multiplier (1.0 to MAX_COMBO_MULTIPLIER)."""
        steps = self._combo // COMBO_STEP
        return min(1.0 + steps * 0.5, MAX_COMBO_MULTIPLIER)

    @property
    def multiplier(self) -> float:
        return self.combo_multiplier()

    def on_correct(self, char_score: int = BASE_POINTS_PER_CHAR) -> int:
        """Handle a correct keystroke."""
        self._combo += 1
        self._max_combo = max(self._max_combo, self._combo)
        points = int(char_score * self.combo_multiplier())
        self._score += points
        return points

    def on_wrong(self) -> None:
        """Handle a wrong keystroke — reset combo."""
        self._combo = 0

    def calculate_cpm(self, correct_chars: int, elapsed_seconds: float) -> float:
        """Calculate characters per minute."""
        if elapsed_seconds <= 0:
            return 0.0
        return correct_chars / elapsed_seconds * 60.0

    def reset(self) -> None:
        self._score = 0
        self._combo = 0
        self._max_combo = 0
