import hashlib
import json
from typing import Generator
from src.materials.scrapers.base_scraper import BaseScraper


class LegalScraper(BaseScraper):
    """Scraper for legal document templates (court clerk practice texts).

    Tries to fetch from open-source legal datasets. Falls back to built-in templates.
    """

    # GitHub open-source legal datasets (Chinese court documents)
    SOURCES = [
        "https://raw.githubusercontent.com/ylanliu/chinese-judicial-documents/main/data/sample.json",
    ]

    def name(self) -> str:
        return "法律文书"

    def category(self) -> str:
        return "legal"

    def _base_url(self) -> str:
        return self.SOURCES[0] if self.SOURCES else ""

    def is_available(self) -> bool:
        """Legal scraper is always available (has built-in fallback)."""
        return True

    def fetch(self, count: int = 20) -> Generator[dict, None, None]:
        # Try online sources first
        yielded = 0
        for source_url in self.SOURCES:
            if yielded >= count:
                break
            try:
                import requests
                resp = requests.get(source_url, timeout=10)
                resp.raise_for_status()
                data = json.loads(resp.text)
                if isinstance(data, list):
                    for item in data[:count]:
                        if yielded >= count:
                            break
                        content = item.get("content", "").strip()
                        if not content or len(content) < 30:
                            continue
                        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                        yielded += 1
                        yield {
                            "title": item.get("title", "法律文书"),
                            "content": content,
                            "author": item.get("author", ""),
                            "category": "legal",
                            "difficulty": self.estimate_difficulty(content),
                            "tags": item.get("tags", ["法律文书"]),
                            "source": source_url,
                            "content_hash": content_hash,
                        }
            except Exception:
                continue

        # Fallback: load from built-in sample_legal.json
        if yielded == 0:
            yield from self._load_builtin(count)

    def _load_builtin(self, count: int) -> Generator[dict, None, None]:
        """Load from local sample_legal.json as fallback."""
        from src.utils.paths import get_data_dir
        builtin_file = get_data_dir() / "sample_legal.json"
        if not builtin_file.exists():
            return
        try:
            with open(builtin_file, "r", encoding="utf-8") as f:
                items = json.load(f)
            for item in items[:count]:
                content = item.get("content", "").strip()
                if not content:
                    continue
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                yield {
                    "title": item.get("title", "法律文书"),
                    "content": content,
                    "author": item.get("author", "法院文书模板"),
                    "category": "legal",
                    "difficulty": item.get("difficulty", self.estimate_difficulty(content)),
                    "tags": item.get("tags", ["法律文书"]),
                    "source": "builtin",
                    "content_hash": content_hash,
                }
        except Exception as e:
            print(f"LegalScraper builtin error: {e}")
