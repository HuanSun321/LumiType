from enum import Enum


class GameState(Enum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    ENDED = "ended"


class GameMode(Enum):
    FOLLOW_TYPING = "follow"
    FALLING_TEXT = "falling"
    TIMED_CHALLENGE = "timed"