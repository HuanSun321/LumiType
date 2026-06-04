import json
import logging
from pathlib import Path

from bs4 import BeautifulSoup

from src.utils.paths import get_data_dir
from .base_scraper import BaseScraper


class LegalScraper(BaseScraper):
    name = "法律法规"
    description = "从国家法律法规数据库获取法律条文素材"
    BASE_URL = "https://flk.npc.gov.cn"
    FALLBACK_FILE = Path(get_data_dir()) / "sample_legal.json"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            headers = {"User-Agent": "TypeHan/1.0 (typing practice app)"}
            resp = self._throttled_get(f"{self.BASE_URL}/", headers=headers)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            seen = set()
            for title_el in soup.select(".item a, a[href*='detail'], a[href*='law']"):
                title = title_el.get_text(" ", strip=True)
                if not title or title in seen:
                    continue
                if len(title) >= 6 and self._looks_like_legal_title(title):
                    seen.add(title)
                    materials.append({
                        "title": title,
                        "content": title,
                        "source": self.name,
                        "category": "legal",
                    })
        except Exception as e:
            logging.warning("LegalScraper: fetch failed: %s", e)
        if not materials:
            materials = self._load_builtin_fallback()
        return materials

    def _load_builtin_fallback(self) -> list[dict]:
        try:
            with self.FALLBACK_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logging.warning("LegalScraper: fallback load failed: %s", e)
            return []

        materials = []
        for item in data:
            content = str(item.get("content", "")).strip()
            title = str(item.get("title", "")).strip()
            if title and content:
                material = dict(item)
                material["title"] = title
                material["content"] = content
                material["source"] = self.name
                material["category"] = "legal"
                materials.append(material)
        return materials

    @staticmethod
    def _looks_like_legal_title(title: str) -> bool:
        keywords = ("法", "条例", "规定", "办法", "决定", "解释", "规则")
        return any(keyword in title for keyword in keywords)
