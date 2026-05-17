from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit,
    QProgressBar, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.materials.material_manager import MaterialManager
from src.materials.material_store import MaterialStore
from src.constants import (
    COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH,
)


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, scraper_type: str, count: int = 50):
        super().__init__()
        self._scraper_type = scraper_type
        self._count = count

    def run(self):
        try:
            if self._scraper_type == "idiom":
                from src.materials.scrapers.idiom_fetcher import IdiomFetcher
                scraper = IdiomFetcher()
            elif self._scraper_type == "poetry":
                from src.materials.scrapers.gushiwen import GushiwenScraper
                scraper = GushiwenScraper()
            elif self._scraper_type == "news":
                from src.materials.scrapers.news_rss import NewsRSSScraper
                scraper = NewsRSSScraper()
            else:
                self.error.emit(f"未知素材源: {self._scraper_type}")
                return

            from src.app import App
            thread_conn = App.instance().db.create_thread_connection()
            store = MaterialStore(conn=thread_conn)
            new_count = 0
            total = 0
            for material in scraper.fetch(self._count):
                total += 1
                if store.save(material):
                    new_count += 1
                self.progress.emit(total, self._count)

            thread_conn.close()
            self.finished.emit(new_count)
        except Exception as e:
            self.error.emit(str(e))


class MaterialScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()

    def on_enter(self, data: dict):
        self._build_ui()

    def _build_ui(self):
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                    item.widget().deleteLater()
        else:
            layout = QVBoxLayout(self)

        layout.setSpacing(14)
        layout.setContentsMargins(36, 24, 36, 24)

        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.setObjectName("back_btn")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.navigate_to("menu") if self.navigate_to else None)
        header.addWidget(back_btn)
        header.addStretch()
        title = QLabel("📚 素材库")
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLOR_ACCENT};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 搜索素材...")
        self._search_input.textChanged.connect(self._filter_materials)
        filter_layout.addWidget(self._search_input, stretch=1)

        self._category_combo = QComboBox()
        self._category_combo.addItems(["全部 📋", "诗词 📝", "成语 📖", "文章 📰"])
        self._category_combo.currentIndexChanged.connect(self._filter_materials)
        filter_layout.addWidget(self._category_combo)

        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["全部", "HSK 1 🌱", "HSK 2 🌿", "HSK 3 🌳", "HSK 4 🎋", "HSK 5 🌲", "HSK 6 🏔️"])
        self._diff_combo.currentIndexChanged.connect(self._filter_materials)
        filter_layout.addWidget(self._diff_combo)

        layout.addLayout(filter_layout)

        # Material list
        self._list = QListWidget()
        layout.addWidget(self._list, stretch=1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._download_combo = QComboBox()
        self._download_combo.addItems(["成语数据集", "古诗文网", "新闻RSS"])
        self._download_combo.setFixedWidth(150)
        btn_layout.addWidget(self._download_combo)

        download_btn = QPushButton("📥 下载素材")
        download_btn.clicked.connect(self._download_materials)
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: 2px solid {COLOR_ACCENT};
                border-radius: 14px;
                padding: 8px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ff7096;
                border-color: #ff7096;
            }}
        """)
        btn_layout.addWidget(download_btn)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(200)
        self._progress_bar.setVisible(False)
        btn_layout.addWidget(self._progress_bar)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._mm = MaterialManager.instance()
        self._filter_materials()

    def _filter_materials(self):
        if not hasattr(self, '_mm'):
            return
        self._list.clear()

        cat_map = {0: None, 1: "poetry", 2: "idiom", 3: "article"}
        category = cat_map.get(self._category_combo.currentIndex())

        diff_map = {0: None, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
        difficulty = diff_map.get(self._diff_combo.currentIndex())

        search = self._search_input.text().strip().lower() if hasattr(self, '_search_input') else ""

        materials = self._mm.get_materials()
        for m in materials:
            if category and m.get("category") != category:
                continue
            if difficulty and m.get("difficulty") != difficulty:
                continue
            if search and search not in m.get("title", "").lower() and search not in m.get("content", "").lower():
                continue

            title = m.get("title", "")
            author = m.get("author", "")
            diff = m.get("difficulty", "?")
            cat = m.get("category", "")
            cat_names = {"poetry": "诗词", "idiom": "成语", "article": "文章"}
            cat_display = cat_names.get(cat, cat)

            text = f"  {title}"
            if author:
                text += f" — {author}"
            text += f"    [HSK {diff}] [{cat_display}]"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, m)
            self._list.addItem(item)

    def _download_materials(self):
        scraper_map = {"成语数据集": "idiom", "古诗文网": "poetry", "新闻RSS": "news"}
        scraper_type = scraper_map.get(self._download_combo.currentText(), "idiom")

        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)

        self._worker = DownloadWorker(scraper_type, count=50)
        self._worker.progress.connect(self._on_download_progress)
        self._worker.finished.connect(self._on_download_finished)
        self._worker.error.connect(self._on_download_error)
        self._worker.start()

    def _on_download_progress(self, current: int, total: int):
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)

    def _on_download_finished(self, new_count: int):
        self._progress_bar.setVisible(False)
        self._mm.reload()
        self._filter_materials()
        QMessageBox.information(self, "下载完成 🎉", f"新增 {new_count} 条素材！")

    def _on_download_error(self, error_msg: str):
        self._progress_bar.setVisible(False)
        QMessageBox.warning(self, "下载失败 😢", f"错误: {error_msg}")
