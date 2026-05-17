from PyQt6.QtCore import QThread, pyqtSignal
from src.app import App
from src.materials.material_store import MaterialStore


class MaterialUpdater(QThread):
    """Silently download new materials on startup in the background."""
    progress = pyqtSignal(int, int)       # (current, total)
    finished = pyqtSignal(int)            # new_count
    error = pyqtSignal(str)

    SCRAPER_MAP = {
        "idiom": ("src.materials.scrapers.idiom_fetcher", "IdiomFetcher"),
        "poetry": ("src.materials.scrapers.gushiwen", "GushiwenScraper"),
        "news":  ("src.materials.scrapers.news_rss", "NewsRSSScraper"),
    }

    def run(self):
        if not App.instance().config.get("auto_update_materials"):
            self.finished.emit(0)
            return

        thread_conn = App.instance().db.create_thread_connection()
        store = MaterialStore(conn=thread_conn)
        total_new = 0

        for name, (module_path, cls_name) in self.SCRAPER_MAP.items():
            try:
                import importlib
                mod = importlib.import_module(module_path)
                scraper_cls = getattr(mod, cls_name)
                scraper = scraper_cls()

                if not scraper.is_available():
                    continue

                count = 0
                for material in scraper.fetch(count=30):
                    if store.save(material):
                        count += 1
                    self.progress.emit(count, 30)
                total_new += count

            except Exception as e:
                continue  # silently skip failed sources

        thread_conn.close()
        self.finished.emit(total_new)
