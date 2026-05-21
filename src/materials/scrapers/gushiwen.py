import logging

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class GushiwenScraper(BaseScraper):
    name = "古诗文网"
    description = "从古诗文网获取古诗词素材"
    BASE_URL = "https://www.gushiwen.cn"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            headers = {"User-Agent": "TypeHan/1.0 (typing practice app)"}
            resp = self._throttled_get(f"{self.BASE_URL}/", headers=headers)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            for item in soup.select(".sons .cont"):
                title_el = item.select_one("b")
                content_el = item.select_one(".contson")
                if not title_el or not content_el:
                    continue
                title = title_el.get_text(strip=True)
                # Remove source tags from content
                for tag in content_el.select("a, .source"):
                    tag.decompose()
                content = content_el.get_text(strip=True)
                if title and content and len(content) >= 10:
                    materials.append({
                        "title": title,
                        "content": content,
                        "source": self.name,
                        "category": "古诗词",
                    })
        except Exception as e:
            logging.warning("GushiwenScraper: fetch failed: %s", e)
        return materials
