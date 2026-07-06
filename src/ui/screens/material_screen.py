import logging

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

logger = logging.getLogger(__name__)


class DownloadWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, scraper_type: str, count: int = 50):
        super().__init__()
        self._scraper_type = scraper_type
        self._count = count

    def _create_scraper(self):
        if self._scraper_type == "idiom":
            from src.materials.scrapers.idiom_fetcher import IdiomFetcher
            return IdiomFetcher()
        if self._scraper_type == "poetry":
            from src.materials.scrapers.gushiwen import GushiwenScraper
            return GushiwenScraper()
        if self._scraper_type == "news":
            from src.materials.scrapers.news_rss import NewsRssScraper
            return NewsRssScraper()
        if self._scraper_type == "legal":
            from src.materials.scrapers.legal_scraper import LegalScraper
            return LegalScraper()
        raise ValueError(f"未知素材源: {self._scraper_type}")

    def run(self):
        thread_conn = None
        try:
            scraper = self._create_scraper()
            from src.app import App
            logger.info(
                "MaterialScreen.download start scraper=%s count=%d",
                type(scraper).__name__,
                self._count,
            )
            thread_conn = App.instance().db.create_thread_connection()
            store = MaterialStore(conn=thread_conn)
            materials = list(scraper.fetch())
            if self._count > 0:
                materials = materials[: self._count]
            total = len(materials)
            new_count = 0
            if total == 0:
                logger.warning(
                    "MaterialScreen.download empty result scraper=%s type=%s",
                    type(scraper).__name__,
                    self._scraper_type,
                )
                self.error.emit("未获取到素材，请检查网络连接或稍后重试。")
                return
            for index, material in enumerate(materials, start=1):
                if store.save(material):
                    new_count += 1
                self.progress.emit(index, total)

            logger.info(
                "MaterialScreen.download done scraper=%s fetched=%d saved=%d",
                type(scraper).__name__,
                total,
                new_count,
            )
            self.finished.emit(new_count)
        except Exception as e:
            logger.exception(
                "MaterialScreen.download failed scraper_type=%s",
                self._scraper_type,
            )
            self.error.emit(f"{self._scraper_type}: {e}")
        finally:
            if thread_conn is not None:
                thread_conn.close()


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
        self._category_combo.addItems(["全部 📋", "诗词 📝", "成语 📖", "文章 📰", "法律 ⚖️", "最近练过 🕘"])
        self._category_combo.currentIndexChanged.connect(self._filter_materials)
        filter_layout.addWidget(self._category_combo)

        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["全部", "HSK 1 🌱", "HSK 2 🌿", "HSK 3 🌳", "HSK 4 🎋", "HSK 5 🌲", "HSK 6 🏔️"])
        self._diff_combo.currentIndexChanged.connect(self._filter_materials)
        filter_layout.addWidget(self._diff_combo)

        self._length_combo = QComboBox()
        self._length_combo.addItems(["全部长度", "短文 <50", "中篇 50-200", "长文 >200"])
        self._length_combo.currentIndexChanged.connect(self._filter_materials)
        filter_layout.addWidget(self._length_combo)

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

        preview_btn = QPushButton("👀 预览")
        preview_btn.clicked.connect(self._preview_selected)
        preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_CREAM};
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
        btn_layout.addWidget(preview_btn)

        fav_btn = QPushButton("⭐ 收藏/取消")
        fav_btn.clicked.connect(self._toggle_favorite)
        fav_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PEACH};
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
        btn_layout.addWidget(fav_btn)

        import_btn = QPushButton("📂 导入本地素材")
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

        cat_map = {0: None, 1: "poetry", 2: "idiom", 3: "article", 4: "legal", 5: "recent"}
        category = cat_map.get(self._category_combo.currentIndex())

        diff_map = {0: None, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
        difficulty = diff_map.get(self._diff_combo.currentIndex())

        search = self._search_input.text().strip().lower() if hasattr(self, '_search_input') else ""
        length_filter = self._length_combo.currentIndex() if hasattr(self, '_length_combo') else 0
        recent_titles = set()
        if category == "recent":
            from src.app import App
            recent_titles = App.instance().db.query_recent_material_titles()
            category = None

        materials = self._mm.get_materials()
        for m in materials:
            if category and m.get("category") != category:
                continue
            if recent_titles and m.get("title", "") not in recent_titles:
                continue
            if self._category_combo.currentIndex() == 5 and not recent_titles:
                continue
            if difficulty and m.get("difficulty") != difficulty:
                continue
            if search and search not in m.get("title", "").lower() and search not in m.get("content", "").lower():
                continue
            length = len(m.get("content", ""))
            if length_filter == 1 and length >= 50:
                continue
            if length_filter == 2 and not (50 <= length <= 200):
                continue
            if length_filter == 3 and length <= 200:
                continue

            title = m.get("title", "")
            author = m.get("author", "")
            diff = m.get("difficulty", "?")
            cat = m.get("category", "")
            cat_names = {"poetry": "诗词", "idiom": "成语", "article": "文章", "news": "新闻", "legal": "法律", "review": "复训"}
            cat_display = cat_names.get(cat, cat)

            star = "★ " if m.get("is_favorite") else ""
            text = f"  {star}{title}"
            if author:
                text += f" — {author}"
            text += f"    [HSK {diff}] [{cat_display}] [{length}字]"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, m)
            self._list.addItem(item)

    def _selected_material(self) -> dict | None:
        selected = self._list.selectedItems() if hasattr(self, '_list') else []
        if not selected:
            return None
        return selected[0].data(Qt.ItemDataRole.UserRole)

    def _preview_selected(self):
        material = self._selected_material()
        if not material:
            QMessageBox.information(self, "预览", "请先选择一条素材。")
            return
        content = material.get("content", "")
        if len(content) > 1200:
            content = content[:1200] + "\n\n……"
        QMessageBox.information(
            self,
            material.get("title", "素材预览"),
            content or "这条素材没有正文。",
        )

    def _toggle_favorite(self):
        material = self._selected_material()
        if not material:
            QMessageBox.information(self, "收藏", "请先选择一条素材。")
            return
        material_id = material.get("id")
        if not material_id:
            QMessageBox.information(self, "收藏", "内置素材暂不支持收藏；下载或导入后可收藏。")
            return
        from src.app import App
        store = MaterialStore(App.instance().db.conn)
        target = not bool(material.get("is_favorite"))
        if store.set_favorite(material_id, target):
            self._mm.reload()
            self._filter_materials()

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
        logger.warning("MaterialScreen.download error=%s", error_msg)
        QMessageBox.warning(self, "下载失败", f"错误: {error_msg}")

    def _import_local_text(self):
        """Import local .txt, .json, .docx, or .doc files as legal practice materials."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择要导入的素材文件", "",
            "素材文件 (*.txt *.json *.docx *.doc);;文本文件 (*.txt *.json);;Word 文件 (*.docx *.doc);;所有文件 (*)"
        )
        if not file_paths:
            return

        from src.app import App
        from src.materials.document_importer import load_local_materials
        from src.materials.material_store import MaterialStore

        thread_conn = App.instance().db.create_thread_connection()
        store = MaterialStore(conn=thread_conn)
        imported = 0

        for file_path in file_paths:
            try:
                for material in load_local_materials(file_path):
                    if store.save(material):
                        imported += 1
            except Exception as e:
                logging.warning("MaterialScreen: import error for %s: %s", file_path, e)
                continue

        thread_conn.close()
        self._mm.reload()
        self._filter_materials()

        if imported > 0:
            QMessageBox.information(self, "导入完成", f"成功导入 {imported} 条法律文书素材！")
        else:
            QMessageBox.warning(self, "导入结果", "未导入任何新素材（可能已存在、文件为空或格式不支持）")
