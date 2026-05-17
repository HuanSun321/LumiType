from src.constants import BASE_POINTS_PER_CHAR, MAX_COMBO_MULTIPLIER, COMBO_STEP


class ScoringEngine:
    def __init__(self):
        self._combo = 0
        self._max_combo = 0
        self._score = 0

    def reset(self):
        self._combo = 0
        self._max_combo = 0
        self._score = 0

    def on_correct(self) -> int:
        self._combo += 1
        self._max_combo = max(self._max_combo, self._combo)
        multiplier = self._current_multiplier()
        points = int(BASE_POINTS_PER_CHAR * multiplier)
        self._score += points
        return points

    def on_wrong(self):
        self._combo = 0

    def _current_multiplier(self) -> float:
        steps = self._combo // COMBO_STEP
        return min(1.0 + steps * 0.5, MAX_COMBO_MULTIPLIER)

    @property
    def combo(self) -> int:
        return self._combo

    @property
    def max_combo(self) -> int:
        return self._max_combo

    @property
    def score(self) -> int:
        return self._score

    @property
    def multiplier(self) -> float:
        return self._current_multiplier()
