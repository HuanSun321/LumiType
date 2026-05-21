import logging

from .base_scraper import BaseScraper


class IdiomFetcher(BaseScraper):
    name = "成语数据集"
    description = "从 chinese-xinhua GitHub 数据集获取成语"
    BASE_URL = "https://raw.githubusercontent.com/pwxcoo/chinese-xinhua/master/data/idiom.json"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            resp = self._throttled_get(self.BASE_URL)
            data = resp.json()
            for item in data:
                word = item.get("word", "")
                if len(word) >= 4 and self._is_cjk(word):
                    materials.append({
                        "title": word,
                        "content": word,
                        "source": self.name,
                        "category": "成语",
                    })
        except Exception as e:
            logging.warning("IdiomFetcher: fetch failed: %s", e)
        return materials

    @staticmethod
    def _is_cjk(text: str) -> bool:
        cjk_count = sum(1 for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF)
        return cjk_count >= len(text) * 0.8