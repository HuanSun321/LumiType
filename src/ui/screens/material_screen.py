from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit,
    QProgressBar, QMessageBox, QFileDialog,
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
            elif self._scraper_type == "legal":
                from src.materials.scrapers.legal_scraper import LegalScraper
                scraper = LegalScraper()
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
        self._category_combo.addItems(["全部 📋", "诗词 📝", "成语 📖", "文章 📰", "法律 ⚖️"])
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
        self._download_combo.addItems(["成语数据集", "古诗文网", "新闻RSS", "法律文书"])
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

        import_btn = QPushButton("📂 导入本地文本")
        import_btn.clicked.connect(self._import_local_text)
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_LAVENDER};
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 14px;
                padding: 8px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border-color: {COLOR_ACCENT};
            }}
        """)
        btn_layout.addWidget(import_btn)

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

        cat_map = {0: None, 1: "poetry", 2: "idiom", 3: "article", 4: "legal"}
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
            cat_names = {"poetry": "诗词", "idiom": "成语", "article": "文章", "legal": "法律"}
            cat_display = cat_names.get(cat, cat)

            text = f"  {title}"
            if author:
                text += f" — {author}"
            text += f"    [HSK {diff}] [{cat_display}]"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, m)
            self._list.addItem(item)

    def _download_materials(self):
        scraper_map = {"成语数据集": "idiom", "古诗文网": "poetry", "新闻RSS": "news", "法律文书": "legal"}
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
        QMessageBox.warning(self, "下载失败", f"错误: {error_msg}")

    def _import_local_text(self):
        """Import local .txt or .json files as legal practice materials."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择要导入的文本文件", "",
            "文本文件 (*.txt *.json);;所有文件 (*)"
        )
        if not file_paths:
            return

        import hashlib
        from src.app import App
        from src.materials.material_store import MaterialStore

        thread_conn = App.instance().db.create_thread_connection()
        store = MaterialStore(conn=thread_conn)
        imported = 0

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()

                if file_path.endswith(".json"):
                    items = __import__("json").loads(text)
                    if isinstance(items, list):
                        for item in items:
                            content = item.get("content", "").strip()
                            if not content:
                                continue
                            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                            mat = {
                                "title": item.get("title", "导入文本"),
                                "content": content,
                                "author": item.get("author", ""),
                                "category": "legal",
                                "difficulty": item.get("difficulty", 3),
                                "tags": item.get("tags", ["法律文书", "导入"]),
                                "source": "local_import",
                                "content_hash": content_hash,
                            }
                            if store.save(mat):
                                imported += 1
                else:
                    # Plain text: split by double newlines as separate entries
                    entries = [e.strip() for e in text.split("\n\n") if e.strip()]
                    if not entries:
                        entries = [text]
                    for entry in entries:
                        lines = entry.split("\n", 1)
                        title = lines[0][:50] if lines else "导入文本"
                        content = entry
                        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                        mat = {
                            "title": title,
                            "content": content,
                            "author": "",
                            "category": "legal",
                            "difficulty": 3,
                            "tags": ["法律文书", "导入"],
                            "source": "local_import",
                            "content_hash": content_hash,
                        }
                        if store.save(mat):
                            imported += 1
            except Exception as e:
                print(f"Import error for {file_path}: {e}")
                continue

        thread_conn.close()
        self._mm.reload()
        self._filter_materials()

        if imported > 0:
            QMessageBox.information(self, "导入完成", f"成功导入 {imported} 条法律文书素材！")
        else:
            QMessageBox.warning(self, "导入结果", "未导入任何新素材（可能已存在或文件格式不正确）")
