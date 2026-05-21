import logging

from src.db.database import DatabaseManager
from src.materials.material_store import MaterialStore
from src.materials.scrapers.gushiwen import GushiwenScraper
from src.materials.scrapers.idiom_fetcher import IdiomFetcher
from src.materials.scrapers.legal_scraper import LegalScraper
from src.materials.scrapers.news_rss import NewsRssScraper


class MaterialUpdater:
    """Background material updater that fetches from all scrapers."""

    SCRAPERS = [GushiwenScraper, IdiomFetcher, LegalScraper, NewsRssScraper]

    def update(self):
        db = DatabaseManager.instance()
        with db.create_thread_connection() as conn:
            store = MaterialStore(conn)
            for scraper_cls in self.SCRAPERS:
                scraper = scraper_cls()
                try:
                    items = scraper.fetch()
                    saved = store.save_batch(items)
                    logging.info(
                        "MaterialUpdater: %s fetched %d items, saved %d",
                        scraper.name, len(items), saved,
                    )
                except Exception as e:
                    logging.warning(
                        "MaterialUpdater: %s failed: %s",
                        scraper.name, e, exc_info=True,
                    )
