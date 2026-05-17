import hashlib
import re
from typing import Generator
import requests
from bs4 import BeautifulSoup
from src.materials.scrapers.base_scraper import BaseScraper


class GushiwenScraper(BaseScraper):
    """Scrape poetry from gushiwen.cn."""

    BASE_URL = "https://www.gushiwen.cn"

    def name(self) -> str:
        return "古诗文网"

    def category(self) -> str:
        return "poetry"

    def _base_url(self) -> str:
        return self.BASE_URL

    def fetch(self, count: int = 20) -> Generator[dict, None, None]:
        try:
            resp = requests.get(f"{self.BASE_URL}/", timeout=15,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            links = []
            for a in soup.select("a[href*='/shiwens/']"):
                href = a.get("href", "")
                if href and href not in links:
                    links.append(href)
                if len(links) >= count:
                    break

            yielded = 0
            for div in soup.select(".sons .cont"):
                if yielded >= count:
                    break
                text_div = div.select_one(".contson")
                if text_div:
                    title_el = div.select_one("b")
                    title = title_el.get_text(strip=True) if title_el else "未知"
                    author_el = div.select_one(".source a")
                    author = author_el.get_text(strip=True) if author_el else ""

                    content = self._clean_content(text_div.get_text())
                    if content and len(content) >= 10:
                        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                        yielded += 1
                        yield {
                            "title": title,
                            "content": content,
                            "author": author,
                            "category": "poetry",
                            "difficulty": self.estimate_difficulty(content),
                            "tags": ["古诗词"],
                            "source": "gushiwen",
                            "content_hash": content_hash,
                        }

        except Exception as e:
            print(f"GushiwenScraper error: {e}")

    def _clean_content(self, text: str) -> str:
        text = re.sub(r'展开阅读全文.*', '', text, flags=re.DOTALL)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[⟪⟫「」『』【】]', '', text)
        return text
