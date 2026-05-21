import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from src.core.game_state import GameState, GameMode
from src.core.scoring import ScoringEngine
from src.constants import TICK_INTERVAL_MS, LOGIC_INTERVAL_MS


class GameEngine(QObject):
    state_changed = pyqtSignal(GameState)
    score_updated = pyqtSignal(int)
    combo_updated = pyqtSignal(int)
    time_updated = pyqtSignal(int)
    game_over = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._state = GameState.IDLE
        self._mode = None
        self._scoring = ScoringEngine()
        self._start_time = 0.0
        self._elapsed = 0.0
        self._paused_elapsed = 0.0

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(TICK_INTERVAL_MS)
        self._tick_timer.timeout.connect(self._on_tick)

        self._logic_timer = QTimer(self)
        self._logic_timer.setInterval(LOGIC_INTERVAL_MS)
        self._logic_timer.timeout.connect(self._on_logic)

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def scoring(self) -> ScoringEngine:
        return self._scoring

    @property
    def elapsed_seconds(self) -> float:
        return self._elapsed

    def start(self, mode):
        self._mode = mode
        self._scoring.reset()
        self._state = GameState.PLAYING
        self._start_time = self._elapsed = 0.0
        self._paused_elapsed = 0.0
        mode.setup(self)
        self._start_time = self._get_time()
        self._tick_timer.start()
        self._logic_timer.start()
        self.state_changed.emit(self._state)

    def pause(self):
        if self._state != GameState.PLAYING:
            return
        self._state = GameState.PAUSED
        self._paused_elapsed = self._get_time() - self._start_time
        self._tick_timer.stop()
        self._logic_timer.stop()
        self.state_changed.emit(self._state)

    def resume(self):
        if self._state != GameState.PAUSED:
            return
        self._state = GameState.PLAYING
        self._start_time = self._get_time() - self._paused_elapsed
        self._tick_timer.start()
        self._logic_timer.start()
        self.state_changed.emit(self._state)

    def end(self):
        if self._state == GameState.ENDED:
            return
        self._state = GameState.ENDED
        self._tick_timer.stop()
        self._logic_timer.stop()
        self._elapsed = self._get_time() - self._start_time
        if self._mode and hasattr(self._mode, "calculate_result"):
            result = self._mode.calculate_result()
        elif self._mode and hasattr(self._mode, "get_result"):
            result = self._mode.get_result()
        else:
            result = {}
        # Engine's elapsed is authoritative (accounts for pauses)
        result["elapsed"] = self._elapsed
        result["score"] = self._scoring.score
        result["max_combo"] = self._scoring.max_combo
        self.game_over.emit(result)
        self.state_changed.emit(self._state)

    def cleanup(self):
        """Stop all timers without emitting signals. Safe to call for early exit."""
        self._tick_timer.stop()
        self._logic_timer.stop()
        if self._state == GameState.PLAYING:
            self._state = GameState.IDLE

    def process_input(self, text: str):
        if self._state == GameState.PLAYING and self._mode:
            self._mode.process_input(text)
            if hasattr(self._mode, "is_game_over") and self._mode.is_game_over():
                self.end()

    def _on_tick(self):
        if self._state == GameState.PLAYING and self._mode:
            self._mode.on_tick(TICK_INTERVAL_MS / 1000.0)
            if hasattr(self._mode, "is_game_over") and self._mode.is_game_over():
                self.end()

    def _on_logic(self):
        if self._state == GameState.PLAYING and self._mode:
            self._elapsed = self._get_time() - self._start_time
            self._mode.on_logic()

    def _get_time(self) -> float:
        return time.time()
