from abc import ABC, abstractmethod
from typing import Generator
import unicodedata


class BaseScraper(ABC):
    """Base class for material scrapers."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def category(self) -> str:
        ...

    @abstractmethod
    def fetch(self, count: int = 20) -> Generator[dict, None, None]:
        ...

    def is_available(self) -> bool:
        import requests
        try:
            resp = requests.head(self._base_url(), timeout=5)
            return resp.status_code < 400
        except Exception:
            return False

    @abstractmethod
    def _base_url(self) -> str:
        ...

    @staticmethod
    def estimate_difficulty(content: str) -> int:
        """Estimate difficulty based on content length and character rarity."""
        if not content:
            return 1
        length = len(content)
        # Count rare CJK characters (Extension B-F, compatibility)
        rare_count = 0
        for ch in content:
            cp = ord(ch)
            if (0x20000 <= cp <= 0x3FFFF or    # CJK Extensions B-F
                0xF900 <= cp <= 0xFAFF or       # CJK Compatibility Ideographs
                0xFE30 <= cp <= 0xFE4F):        # CJK Compatibility Forms
                rare_count += 1
        rare_ratio = rare_count / max(length, 1)

        # Length factor
        if length <= 20:
            length_score = 1
        elif length <= 50:
            length_score = 2
        elif length <= 100:
            length_score = 3
        elif length <= 200:
            length_score = 4
        else:
            length_score = 5

        # Rarity factor
        if rare_ratio > 0.3:
            rarity_bonus = 2
        elif rare_ratio > 0.1:
            rarity_bonus = 1
        else:
            rarity_bonus = 0

        return min(6, max(1, length_score + rarity_bonus))
