import json
import logging
from pathlib import Path

from src.utils.paths import get_data_dir
from .base_scraper import BaseScraper


class IdiomFetcher(BaseScraper):
    name = "成语数据集"
    description = "从本地内置成语包加载成语"
    DATA_FILE = Path(get_data_dir()) / "common_idioms.json"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            if not self.DATA_FILE.exists():
                raise FileNotFoundError(f"missing built-in idiom file: {self.DATA_FILE}")
            with self.DATA_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                word = item.get("word", "")
                if len(word) >= 4 and self._is_cjk(word):
                    materials.append({
                        "title": word,
                        "content": word,
                        "source": self.name,
                        "category": "idiom",
                    })
        except Exception:
            logging.exception("IdiomFetcher: fetch failed")
            raise
        return materials

    @staticmethod
    def _is_cjk(text: str) -> bool:
        cjk_count = sum(1 for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF)
        return cjk_count >= len(text) * 0.8
