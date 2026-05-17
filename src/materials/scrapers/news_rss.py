import hashlib
from typing import Generator
import feedparser
from bs4 import BeautifulSoup
from src.materials.scrapers.base_scraper import BaseScraper


class NewsRSSScraper(BaseScraper):
    """Fetch news articles from RSS feeds for typing practice."""

    FEEDS = [
        "https://feedx.net/rss/people.xml",
        "https://feedx.net/rss/xinhuanet.xml",
        "https://rsshub.app/cls/telegraph",
    ]

    def name(self) -> str:
        return "新闻RSS"

    def category(self) -> str:
        return "news"

    def _base_url(self) -> str:
        return self.FEEDS[0]

    def fetch(self, count: int = 20) -> Generator[dict, None, None]:
        for feed_url in self.FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:count]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", entry.get("description", "")).strip()
                    content = self._clean_html(summary)

                    if not content or len(content) < 20:
                        continue

                    if len(content) > 500:
                        content = self._truncate_at_boundary(content, 500)

                    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    yield {
                        "title": title,
                        "content": content,
                        "author": entry.get("author", ""),
                        "category": "news",
                        "difficulty": self.estimate_difficulty(content),
                        "tags": ["新闻"],
                        "source": feed_url,
                        "content_hash": content_hash,
                    }
            except Exception as e:
                print(f"NewsRSSScraper error for {feed_url}: {e}")
                continue

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags using BeautifulSoup for robustness."""
        try:
            soup = BeautifulSoup(text, "html.parser")
            return soup.get_text(separator=" ")
        except Exception:
            # Fallback to regex if BS4 fails
            import re
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'&\w+;', ' ', text)
            return text

    @staticmethod
    def _truncate_at_boundary(text: str, max_len: int) -> str:
        """Truncate at sentence boundary instead of mid-character."""
        if len(text) <= max_len:
            return text
        truncated = text[:max_len]
        # Try to cut at last sentence-ending punctuation
        for sep in ('。', '！', '？', '；', '.', '!', '?', '；'):
            idx = truncated.rfind(sep)
            if idx > max_len // 2:
                return truncated[:idx + 1]
        return truncated
