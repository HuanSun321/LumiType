import html
import logging
import re

import feedparser
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class NewsRssScraper(BaseScraper):
    name = "新闻RSS"
    description = "从RSS源获取新闻素材"
    BASE_URL = "http://www.people.com.cn/rss/ywkx.xml"
    FULL_ARTICLE_THRESHOLD = 80
    REQUEST_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def fetch(self) -> list[dict]:
        materials = []
        try:
            resp = self._throttled_get(self.BASE_URL, headers=self.REQUEST_HEADERS)
            resp.encoding = "utf-8"
            feed = feedparser.parse(resp.text)

            for entry in feed.entries:
                title = getattr(entry, "title", "").strip()
                raw_content = getattr(entry, "summary", "") or getattr(entry, "description", "")
                content = self._clean_rss_content(raw_content)
                link = getattr(entry, "link", "").strip()
                if link and len(content) < self.FULL_ARTICLE_THRESHOLD:
                    article_content = self._fetch_article_content(link)
                    if len(article_content) > len(content):
                        content = article_content
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

    @staticmethod
    def _clean_rss_content(raw_content: str) -> str:
        content = html.unescape(raw_content or "")
        content = re.sub(r"<[^>]+>", "", content)
        return re.sub(r"\s+", " ", content).strip()

    def _fetch_article_content(self, url: str) -> str:
        try:
            resp = self._throttled_get(url, headers=self.REQUEST_HEADERS)
            if not getattr(resp, "encoding", None):
                resp.encoding = "utf-8"
            return self._extract_article_text(resp.text)
        except Exception as e:
            logging.warning("NewsRssScraper: article fetch failed url=%s error=%s", url, e)
            return ""

    @staticmethod
    def _extract_article_text(page_html: str) -> str:
        soup = BeautifulSoup(page_html or "", "html.parser")
        for tag in soup.select("script, style, noscript"):
            tag.decompose()

        selectors = [
            "article",
            "#rwb_zw",
            ".rm_txt_con",
            ".artDet",
            ".article",
            ".content",
            ".text",
            ".box_con",
            ".show_text",
        ]
        candidates = [node for selector in selectors for node in soup.select(selector)]
        candidates.append(soup.body or soup)

        best = ""
        for node in candidates:
            paragraphs = node.find_all("p")
            texts = [NewsRssScraper._clean_article_line(p.get_text(" ", strip=True)) for p in paragraphs]
            content = "\n".join(line for line in texts if line)
            if len(content) > len(best):
                best = content
        return best

    @staticmethod
    def _clean_article_line(line: str) -> str:
        line = re.sub(r"\s+", " ", line or "").strip()
        if not line:
            return ""
        noise_markers = ("责任编辑", "责编", "来源：", "分享到", "扫一扫", "客户端")
        if any(marker in line for marker in noise_markers):
            return ""
        return line
