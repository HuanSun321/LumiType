import html
import logging

import feedparser

from .base_scraper import BaseScraper


class NewsRssScraper(BaseScraper):
    name = "新闻RSS"
    description = "从RSS源获取新闻素材"
    BASE_URL = "https://feedx.net/rss/people.xml"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            resp = self._throttled_get(self.BASE_URL)
            feed = feedparser.parse(resp.text)

            for entry in feed.entries:
                title = getattr(entry, "title", "").strip()
                # Sanitize HTML content from RSS
                raw_content = getattr(entry, "summary", "") or getattr(entry, "description", "")
                content = html.unescape(raw_content)
                # Strip HTML tags
                import re
                content = re.sub(r"<[^>]+>", "", content).strip()
                if title and content and len(content) >= 10:
                    materials.append({
                        "title": title,
                        "content": content,
                        "source": self.name,
                        "category": "新闻",
                    })
        except Exception as e:
            logging.warning("NewsRssScraper: fetch failed: %s", e)
        return materials
