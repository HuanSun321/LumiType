import logging

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class LegalScraper(BaseScraper):
    name = "法律法规"
    description = "从法律法规网站获取法律条文素材"
    BASE_URL = "https://www.pkulaw.com"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            headers = {"User-Agent": "TypeHan/1.0 (typing practice app)"}
            resp = self._throttled_get(f"{self.BASE_URL}/", headers=headers)
            resp.encoding = "utf-8"
            soup = BeautifulSoup(resp.text, "html.parser")

            for item in soup.select(".item"):
                title_el = item.select_one("a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                content = title_el.get("title", "") or title
                if title and len(content) >= 10:
                    materials.append({
                        "title": title,
                        "content": content,
                        "source": self.name,
                        "category": "法律",
                    })
        except Exception as e:
            logging.warning("LegalScraper: fetch failed: %s", e)
        return materials
