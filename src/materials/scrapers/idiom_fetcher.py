import json
import hashlib
from typing import Generator
import requests
from src.materials.scrapers.base_scraper import BaseScraper


class IdiomFetcher(BaseScraper):
    """Fetch Chinese idioms from the pwxcoo/chinese-xinhua GitHub dataset."""

    DATA_URL = "https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json"
    MAX_RETRIES = 3

    def name(self) -> str:
        return "成语数据集"

    def category(self) -> str:
        return "idiom"

    def _base_url(self) -> str:
        return self.DATA_URL

    def fetch(self, count: int = 50) -> Generator[dict, None, None]:
        data = None
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = requests.get(self.DATA_URL, timeout=15)
                resp.raise_for_status()
                data = json.loads(resp.text)
                break
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    print(f"IdiomFetcher error after {self.MAX_RETRIES} retries: {e}")
                    return

        suitable = [
            item for item in data
            if len(item.get("word", "")) >= 4
            and self._is_cjk_content(item.get("word", ""))
        ]

        for item in suitable[:count]:
            word = item.get("word", "")
            content_hash = hashlib.sha256(word.encode("utf-8")).hexdigest()
            yield {
                "title": word,
                "content": word,
                "author": "",
                "category": "idiom",
                "difficulty": self.estimate_difficulty(word),
                "tags": ["成语"],
                "source": "chinese-xinhua",
                "content_hash": content_hash,
            }

    def _is_cjk_content(self, text: str) -> bool:
        cjk_count = sum(1 for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF)
        return cjk_count >= len(text) * 0.8
