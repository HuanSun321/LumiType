import html
import logging
import re

import feedparser

from .base_scraper import BaseScraper


class NewsRssScraper(BaseScraper):
    name = "新闻RSS"
    description = "从RSS源获取新闻素材"
    BASE_URL = "http://www.people.com.cn/rss/ywkx.xml"

    def fetch(self) -> list[dict]:
        materials = []
        try:
            resp = self._throttled_get(self.BASE_URL)
            resp.encoding = "utf-8"
            feed = feedparser.parse(resp.text)

            for entry in feed.entries:
                title = getattr(entry, "title", "").strip()
                raw_content = getattr(entry, "summary", "") or getattr(entry, "description", "")
                content = html.unescape(raw_content)
                content = re.sub(r"<[^>]+>", "", content).strip()
                if not content:
                    content = title
                if title and content and len(content) >= 10:
                    materials.append({
                        "title": title,
                        "content": content,
                        "source": self.name,
                        "category": "news",
                    })
        except Exception as e:
            logging.warning("NewsRssScraper: fetch failed: %s", e)
        return materials
