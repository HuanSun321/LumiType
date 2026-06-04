import unittest
import sqlite3


def ensure_qt_app():
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    try:
        from src.app import App
        App.instance()
    except RuntimeError:
        from src.app import App
        App(app)
    return app


class RuntimeContractTests(unittest.TestCase):
    def test_builtin_data_dir_points_to_json_files(self):
        from src.utils.paths import get_data_dir

        data_dir = get_data_dir()
        self.assertTrue(data_dir.name == "builtin")
        self.assertTrue((data_dir / "sample_poems.json").exists())

    def test_material_manager_keeps_legacy_api(self):
        from src.materials.material_manager import MaterialManager

        manager = MaterialManager.instance()
        materials = manager.get_materials()
        self.assertGreater(len(materials), 0)
        self.assertGreater(manager.count, 0)
        self.assertIsInstance(manager.get_random_material(), dict)

    def test_config_manager_has_ui_defaults(self):
        from src.config import ConfigManager

        config = ConfigManager.instance()
        self.assertIsInstance(config.get("window_width"), int)
        self.assertIsInstance(config.get("window_height"), int)
        self.assertIsInstance(config.get("font_size"), int)
        self.assertIsInstance(config.get("sound_enabled"), bool)
        self.assertIsInstance(config.get("keyboard_rabbit_scale"), int)

    def test_modes_keep_game_screen_contract(self):
        from src.modes.follow_typing import FollowTypingMode
        from src.modes.timed_challenge import TimedChallengeMode
        from src.modes.falling_text import FallingTextMode

        follow = FollowTypingMode(category=None, ratio=1.0)
        timed = TimedChallengeMode(category=None, ratio=1.0)
        falling = FallingTextMode(category=None, ratio=1.0)

        self.assertTrue(follow.text)
        self.assertTrue(hasattr(follow, "cursor_position"))
        self.assertTrue(hasattr(follow, "current_cpm"))
        self.assertTrue(hasattr(timed, "duration"))
        self.assertTrue(hasattr(timed, "material"))
        self.assertTrue(hasattr(falling, "get_widget"))
        self.assertTrue(falling.text)

    def test_game_engine_accepts_mode_contract(self):
        from src.core.game_engine import GameEngine
        from src.modes.follow_typing import FollowTypingMode

        engine = GameEngine()
        mode = FollowTypingMode(category=None, ratio=1.0)
        engine.start(mode)
        engine.process_input(mode.text[:1])
        engine.end()

        self.assertEqual(engine.state.value, "ended")

    def test_poetry_layout_preserves_couplet_line_breaks(self):
        ensure_qt_app()
        from src.ui.widgets.text_display import TextDisplayWidget

        widget = TextDisplayWidget()
        widget.resize(360, 260)
        widget.set_material({
            "title": "诗词测试",
            "author": "测试",
            "category": "poetry",
            "content": "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。",
        })
        widget._recalc_layout()

        self.assertTrue(widget._char_positions)
        lines = {round(y) for _, _, y in widget._char_positions}
        self.assertEqual(len(lines), 2)

    def test_long_ci_text_uses_prose_layout(self):
        ensure_qt_app()
        from src.ui.widgets.text_display import TextDisplayWidget

        widget = TextDisplayWidget()
        widget.resize(480, 320)
        widget.set_material({
            "title": "水调歌头",
            "author": "苏轼",
            "category": "poetry",
            "content": "明月几时有？把酒问青天。不知天上宫阙，今夕是何年。"
                       "我欲乘风归去，又恐琼楼玉宇，高处不胜寒。",
        })

        self.assertEqual(widget._layout_mode, "prose")

    def test_keyboard_rabbit_supports_runtime_scale(self):
        ensure_qt_app()
        from src.ui.widgets.keyboard_rabbit import KeyboardRabbitWidget

        rabbit = KeyboardRabbitWidget()
        rabbit.set_scale_percent(60)
        small_size = rabbit.size()
        rabbit.set_scale_percent(120)
        large_size = rabbit.size()

        self.assertLess(small_size.width(), large_size.width())
        self.assertLess(small_size.height(), large_size.height())

    def test_keyboard_rabbit_paints_effect_colors(self):
        ensure_qt_app()
        from PyQt6.QtGui import QPainter, QPixmap
        from src.ui.widgets.keyboard_rabbit import KeyboardRabbitWidget

        rabbit = KeyboardRabbitWidget()
        pixmap = QPixmap(rabbit.size())
        pixmap.fill()
        painter = QPainter(pixmap)
        rabbit.set_expression("combo")
        rabbit.render(painter)
        rabbit.set_expression("wrong")
        rabbit.render(painter)
        painter.end()

        self.assertFalse(pixmap.isNull())

    def test_falling_mode_accepts_direct_chinese_commit(self):
        ensure_qt_app()
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import QGraphicsScene
        from src.modes.falling_text import FallingTextMode
        from src.ui.widgets.falling_item import FallingCharItem

        mode = FallingTextMode(category=None, ratio=1.0)
        mode._scene = QGraphicsScene()
        item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="")
        mode._scene.addItem(item)
        mode._items.add(item)

        result = mode.process_input("归")

        self.assertTrue(result["hit"])
        self.assertEqual(item.state, FallingCharItem.STATE_ELIMINATED)
        self.assertIsNone(item.scene())
        self.assertNotIn(item, mode._items)
        self.assertEqual(mode.get_result()["correct_chars"], 1)

    def test_falling_mode_accepts_exact_pinyin_preedit(self):
        ensure_qt_app()
        from PyQt6.QtGui import QFont
        from src.modes.falling_text import FallingTextMode
        from src.ui.widgets.falling_item import FallingCharItem

        mode = FallingTextMode(category=None, ratio=1.0)
        mode._pinyin_map = {"归": ["gui"]}
        item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="gui")
        mode._items.add(item)

        mode.process_composing("gui")

        self.assertEqual(item.state, FallingCharItem.STATE_ELIMINATED)
        self.assertEqual(mode.get_result()["correct_chars"], 1)

    def test_falling_mode_reports_missing_pypinyin(self):
        from unittest.mock import patch
        from src.modes.falling_text import FallingTextMode

        original_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "pypinyin":
                raise ImportError("blocked pypinyin")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            mode = FallingTextMode(category=None, ratio=1.0)

        self.assertFalse(mode.pinyin_available)
        self.assertIn("pypinyin", mode.pinyin_error)

    def test_falling_mode_does_not_use_fallback_content_pool(self):
        from unittest.mock import patch
        from src.modes.falling_text import FallingTextMode

        with patch("src.modes.falling_text.MaterialManager") as material_manager:
            material_manager.instance.return_value.get_materials.return_value = []
            mode = FallingTextMode(category=None, ratio=1.0)

        self.assertEqual(mode.text, "")
        self.assertFalse(mode.pinyin_available)
        self.assertIn("materials", mode.pinyin_error)

    def test_falling_pinyin_buffer_recovers_after_invalid_prefix(self):
        ensure_qt_app()
        from PyQt6.QtGui import QFont
        from src.modes.falling_text import FallingTextMode
        from src.ui.widgets.falling_item import FallingCharItem

        mode = FallingTextMode(category=None, ratio=1.0)
        mode._pinyin_map = {"归": ["gui"]}
        item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="gui")
        mode._items.add(item)

        mode.process_input("x")
        mode.process_input("g")
        mode.process_input("u")
        result = mode.process_input("i")

        self.assertTrue(result["hit"])
        self.assertEqual(item.state, FallingCharItem.STATE_ELIMINATED)
        self.assertEqual(mode.current_pinyin, "")

    def test_falling_ignores_ime_commit_after_preedit_hit(self):
        ensure_qt_app()
        from PyQt6.QtGui import QFont
        from src.modes.falling_text import FallingTextMode
        from src.ui.widgets.falling_item import FallingCharItem

        mode = FallingTextMode(category=None, ratio=1.0)
        mode._pinyin_map = {"归": ["gui"]}
        item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="gui")
        mode._items.add(item)

        mode.process_composing("gui")
        mode.process_input("贵")

        result = mode.get_result()
        self.assertEqual(result["total_chars"], 1)
        self.assertEqual(result["correct_chars"], 1)

    def test_falling_view_uses_full_repaint_to_prevent_outline_trails(self):
        ensure_qt_app()
        from PyQt6.QtWidgets import QGraphicsView
        from src.constants import COLOR_SKY
        from src.modes.falling_text import FallingTextMode

        mode = FallingTextMode(category=None, ratio=1.0)
        mode.get_widget()

        self.assertEqual(
            mode._view.viewportUpdateMode(),
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate,
        )
        self.assertIn(COLOR_SKY, mode._view.styleSheet())

    def test_input_bar_direct_mode_emits_ascii_keypresses_before_ime_commit(self):
        ensure_qt_app()
        from PyQt6.QtTest import QTest
        from src.ui.widgets.input_bar import InputBar

        input_bar = InputBar()
        emitted = []
        input_bar.text_committed.connect(emitted.append)
        input_bar.set_direct_mode(True)
        input_bar.show()
        input_bar.setFocus()

        QTest.keyClicks(input_bar._line_edit, "gui")

        self.assertEqual(emitted, ["g", "u", "i"])

    def test_timed_hud_formats_remaining_seconds_as_integer(self):
        ensure_qt_app()
        from src.core.game_state import GameMode
        from src.ui.screens.game_screen import GameScreen

        screen = GameScreen()
        screen.on_enter({"mode": GameMode.TIMED_CHALLENGE.value, "category": "poetry"})
        screen._mode.time_remaining = 113.23199999999974
        screen._update_hud()

        self.assertEqual(screen._timer_label.text(), "⏰ 114s")

    def test_falling_screen_blocks_when_pinyin_dependency_missing(self):
        ensure_qt_app()
        from unittest.mock import patch
        from src.core.game_state import GameMode
        from src.ui.screens.game_screen import GameScreen

        class NoPinyinMode:
            pinyin_available = False
            pinyin_error = "pypinyin missing"
            text = "归"

        screen = GameScreen()
        navigations = []
        screen.navigate_to = lambda name, data=None: navigations.append(name)

        with patch("src.ui.screens.game_screen.FallingTextMode", return_value=NoPinyinMode()):
            with patch("PyQt6.QtWidgets.QMessageBox.warning") as warning:
                screen.on_enter({"mode": GameMode.FALLING_TEXT.value})

        self.assertTrue(warning.called)
        self.assertEqual(navigations, ["menu"])

    def test_falling_deco_setting_controls_frame_pattern(self):
        ensure_qt_app()
        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QFont, QPainter, QPixmap
        from src.app import App
        from src.ui.widgets.falling_item import FallingCharItem

        config = App.instance().config
        previous = config.get("falling_deco")
        try:
            config.set("falling_deco", "heart")
            heart_item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="gui")
            heart_path = heart_item._frame_path(QRectF(0, 0, 90, 90))

            config.set("falling_deco", "star")
            star_item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="gui")
            star_path = star_item._frame_path(QRectF(0, 0, 90, 90))

            self.assertEqual(heart_item._frame_type, "heart")
            self.assertEqual(star_item._frame_type, "star")
            self.assertNotEqual(heart_path.elementCount(), star_path.elementCount())

            pixmap = QPixmap(120, 120)
            pixmap.fill()
            painter = QPainter(pixmap)
            heart_item.paint(painter, None)
            painter.end()
            self.assertFalse(pixmap.isNull())
        finally:
            config.set("falling_deco", previous)

    def test_falling_frame_bounds_include_character_and_pinyin(self):
        ensure_qt_app()
        from PyQt6.QtGui import QFont
        from src.app import App
        from src.ui.widgets.falling_item import DECO_TYPES, FallingCharItem

        config = App.instance().config
        previous = config.get("falling_deco")
        try:
            for frame_type in DECO_TYPES:
                config.set("falling_deco", frame_type)
                item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="zhong")

                frame_bounds = item._frame_path(item._frame_rect()).boundingRect()
                text_bounds = item._text_bounds().adjusted(-4, -3, 4, 3)

                self.assertTrue(
                    frame_bounds.contains(text_bounds),
                    f"{frame_type} frame {frame_bounds} does not contain text {text_bounds}",
                )
        finally:
            config.set("falling_deco", previous)

    def test_falling_frame_resizes_without_stretching_shape(self):
        ensure_qt_app()
        from PyQt6.QtGui import QFont
        from src.app import App
        from src.ui.widgets.falling_item import DECO_TYPES, FallingCharItem

        config = App.instance().config
        previous = config.get("falling_deco")
        try:
            for frame_type in DECO_TYPES:
                config.set("falling_deco", frame_type)
                item = FallingCharItem("归", 0, 0, 10, QFont("Microsoft YaHei", 22), pinyin="zhong")
                frame_rect = item._frame_rect()

                self.assertAlmostEqual(
                    frame_rect.width(),
                    frame_rect.height(),
                    delta=0.01,
                    msg=f"{frame_type} frame rect was stretched: {frame_rect}",
                )
        finally:
            config.set("falling_deco", previous)

    def test_main_window_uses_translucent_shell(self):
        ensure_qt_app()
        from PyQt6.QtCore import Qt
        from src.ui.main_window import MainWindow

        window = MainWindow()
        self.assertTrue(window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertEqual(window.centralWidget().objectName(), "windowShell")
        window._is_fullscreen = False
        window._sync_window_shape()
        self.assertTrue(window.mask().isEmpty())
        window._is_fullscreen = True
        window._sync_window_shape()
        self.assertTrue(window.mask().isEmpty())
        window.close()

    def test_settings_combo_popups_use_light_views(self):
        ensure_qt_app()
        from src.ui.screens.settings_screen import SettingsScreen

        screen = SettingsScreen()
        screen.on_enter({})

        combo_names = ("_font_combo", "_timed_combo", "_deco_combo", "_res_combo")
        for name in combo_names:
            combo = getattr(screen, name)
            self.assertIn("background-color: #FFFFFF", combo.view().styleSheet())

    def test_stats_summary_cards_keep_equal_row_structure(self):
        ensure_qt_app()
        from src.ui.screens.stats_screen import _summary_card

        with_change = _summary_card("A", "0", "*", "#fff", "-", True)
        without_change = _summary_card("B", "0 day", "*", "#fff", "", True)

        self.assertEqual(with_change.count(), without_change.count())
        self.assertEqual(with_change.count(), 4)
        for index in range(4):
            self.assertEqual(
                with_change.itemAt(index).widget().height(),
                without_change.itemAt(index).widget().height(),
            )

    def test_stats_screen_reuses_layout_and_refreshes_saved_results(self):
        ensure_qt_app()
        from src.app import App
        from src.db.database import DatabaseManager
        from src.ui.screens.stats_screen import StatsScreen

        manager = DatabaseManager.__new__(DatabaseManager)
        manager._conn = sqlite3.connect(":memory:")
        manager._conn.row_factory = sqlite3.Row
        manager._run_migrations()

        app = App.instance()
        original_db = app._db
        screen = None
        try:
            manager.save_game_result({
                "mode": "follow",
                "elapsed": 10,
                "total_chars": 10,
                "correct_chars": 8,
                "accuracy": 0.8,
                "cpm": 48,
                "score": 80,
                "max_combo": 8,
                "material_title": "stats test",
            })
            app._db = manager

            screen = StatsScreen()
            screen.on_enter({})
            first_layout = screen.layout()
            screen.on_enter({})

            summary = screen._summary_layout.itemAt(0).layout()
            self.assertIs(screen.layout(), first_layout)
            self.assertEqual(summary.itemAt(1).widget().text(), "1")
            self.assertEqual(screen._table.rowCount(), 1)
        finally:
            app._db = original_db
            manager.close()
            if screen:
                screen.deleteLater()

    def test_stats_screen_uses_scroll_area_and_fixed_footer_at_1080p(self):
        ensure_qt_app()
        from PyQt6.QtWidgets import QScrollArea
        from src.ui.screens.stats_screen import StatsScreen

        screen = StatsScreen()
        try:
            screen.resize(1920, 1080)
            screen.on_enter({})

            self.assertTrue(hasattr(screen, "_scroll"))
            self.assertIsInstance(screen._scroll, QScrollArea)
            self.assertTrue(hasattr(screen, "_footer"))
            self.assertTrue(hasattr(screen, "_clear_btn"))
            self.assertIs(screen._clear_btn.parentWidget(), screen._footer)
            self.assertIsNot(screen._clear_btn.parentWidget(), screen._table)
            self.assertGreaterEqual(screen._clear_btn.minimumHeight(), 40)
        finally:
            screen.deleteLater()

    def test_fullscreen_content_uses_consistent_center_width(self):
        ensure_qt_app()
        from src.ui.screens.settings_screen import SettingsScreen
        from src.ui.screens.stats_screen import StatsScreen

        settings = SettingsScreen()
        stats = StatsScreen()
        try:
            for screen in (settings, stats):
                screen.resize(2048, 1200)
                screen.on_enter({})
                screen._sync_content_width()
                self.assertEqual(screen._content.width(), 1180)
        finally:
            settings.deleteLater()
            stats.deleteLater()

    def test_follow_typing_ignores_extra_input_after_game_over(self):
        ensure_qt_app()
        from src.core.game_state import GameMode
        from src.ui.screens.game_screen import GameScreen

        screen = GameScreen()
        screen.on_enter({"mode": GameMode.FOLLOW_TYPING.value, "category": "poetry"})
        text = screen._mode.text
        for ch in text:
            screen._on_input(ch)
        screen._on_input("多")

        self.assertEqual(screen._engine.state.value, "ended")

    def test_follow_typing_records_mistake_details(self):
        from src.modes.follow_typing import FollowTypingMode

        mode = FollowTypingMode(material={
            "title": "错字测试",
            "category": "article",
            "content": "天地",
        })
        mode.start()
        mode.process_input("大")

        self.assertEqual(len(mode.mistake_events), 1)
        event = mode.mistake_events[0]
        self.assertEqual(event["expected"], "天")
        self.assertEqual(event["actual"], "大")
        self.assertEqual(event["position"], 0)
        self.assertEqual(event["context"], "天地")

    def test_follow_typing_material_matches_truncated_practice_text(self):
        from src.modes.follow_typing import FollowTypingMode

        text = "一二三四五六七八九十" * 10
        mode = FollowTypingMode(ratio=0.1, material={
            "title": "长文截断测试",
            "category": "article",
            "content": text,
        })

        self.assertEqual(len(mode.text), 10)
        self.assertEqual(mode.material["content"], mode.text)

    def test_database_saves_mistakes_and_builds_review_material(self):
        from src.db.database import DatabaseManager

        manager = DatabaseManager.__new__(DatabaseManager)
        manager._conn = sqlite3.connect(":memory:")
        manager._conn.row_factory = sqlite3.Row
        manager._run_migrations()

        try:
            result_id = manager.save_game_result({
                "mode": "follow",
                "elapsed": 6,
                "total_chars": 2,
                "correct_chars": 1,
                "accuracy": 0.5,
                "cpm": 10,
                "score": 10,
                "max_combo": 1,
                "material_title": "错字测试",
            })
            manager.save_typing_mistakes(result_id, [
                {"expected": "天", "actual": "大", "position": 0, "context": "天地"},
                {"expected": "地", "actual": "池", "position": 1, "context": "天地"},
                {"expected": "天", "actual": "夫", "position": 0, "context": "天地"},
            ], {"mode": "follow", "material_title": "错字测试"})

            top = manager.query_top_mistakes(limit=2)
            self.assertEqual(top[0]["expected"], "天")
            self.assertEqual(top[0]["count"], 2)

            review = manager.build_review_material(limit=8)
            self.assertEqual(review["title"], "今日错字复训")
            self.assertIn("天", review["content"])
            self.assertIn("地", review["content"])
        finally:
            manager.close()

    def test_review_material_repeats_sparse_mistakes_enough_for_practice(self):
        from src.db.database import DatabaseManager

        manager = DatabaseManager.__new__(DatabaseManager)
        manager._conn = sqlite3.connect(":memory:")
        manager._conn.row_factory = sqlite3.Row
        manager._run_migrations()

        try:
            result_id = manager.save_game_result({
                "mode": "follow",
                "elapsed": 3,
                "total_chars": 1,
                "correct_chars": 0,
                "accuracy": 0,
                "cpm": 0,
                "score": 0,
                "max_combo": 0,
                "material_title": "短错字测试",
            })
            manager.save_typing_mistakes(result_id, [
                {"expected": "天", "actual": "大", "position": 0, "context": "天地"},
            ], {"mode": "follow", "material_title": "短错字测试"})

            review = manager.build_review_material()

            self.assertGreaterEqual(len(review["content"]), 24)
            self.assertEqual(set(review["content"]), {"天"})
        finally:
            manager.close()

    def test_material_store_can_toggle_favorite(self):
        from src.db.database import DatabaseManager
        from src.materials.material_store import MaterialStore

        manager = DatabaseManager.__new__(DatabaseManager)
        manager._conn = sqlite3.connect(":memory:")
        manager._conn.row_factory = sqlite3.Row
        manager._run_migrations()
        store = MaterialStore(manager.conn)

        try:
            self.assertTrue(store.save({
                "source": "test",
                "category": "article",
                "title": "收藏测试",
                "content": "收藏这一段文字",
                "difficulty": 1,
            }))
            material = store.get_all(limit=1)[0]

            self.assertTrue(store.set_favorite(material["id"], True))
            favorite = store.get_all(limit=1)[0]
            self.assertEqual(favorite["is_favorite"], 1)
        finally:
            manager.close()

    def test_material_download_worker_uses_fetch_without_count_argument(self):
        ensure_qt_app()
        from unittest.mock import Mock, patch
        from src.materials.scrapers.idiom_fetcher import IdiomFetcher
        from src.ui.screens.material_screen import DownloadWorker

        class DummyConn:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        conn = DummyConn()
        app_stub = Mock()
        app_stub.db.create_thread_connection.return_value = conn
        store_stub = Mock()
        store_stub.save.return_value = True
        worker = DownloadWorker("idiom", count=50)
        errors = []
        finished = []
        progress = []
        worker.error.connect(errors.append)
        worker.finished.connect(finished.append)
        worker.progress.connect(lambda current, total: progress.append((current, total)))

        with patch("src.app.App.instance", return_value=app_stub):
            with patch("src.ui.screens.material_screen.MaterialStore", return_value=store_stub):
                with patch.object(IdiomFetcher, "fetch", autospec=True, return_value=[{
                    "title": "成语测试",
                    "content": "一帆风顺",
                    "source": "成语数据集",
                    "category": "idiom",
                }]) as fetch:
                    worker.run()

        fetch.assert_called_once()
        self.assertEqual(len(fetch.call_args.args), 1)
        self.assertEqual(errors, [])
        self.assertEqual(finished, [1])
        self.assertEqual(progress, [(1, 1)])
        self.assertTrue(conn.closed)

    def test_material_download_worker_news_branch_does_not_crash(self):
        ensure_qt_app()
        from unittest.mock import Mock, patch
        from src.materials.scrapers.news_rss import NewsRssScraper
        from src.ui.screens.material_screen import DownloadWorker

        class DummyConn:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        conn = DummyConn()
        app_stub = Mock()
        app_stub.db.create_thread_connection.return_value = conn
        store_stub = Mock()
        store_stub.save.return_value = True
        worker = DownloadWorker("news", count=50)
        errors = []
        finished = []
        worker.error.connect(errors.append)
        worker.finished.connect(finished.append)

        with patch("src.app.App.instance", return_value=app_stub):
            with patch("src.ui.screens.material_screen.MaterialStore", return_value=store_stub):
                with patch.object(NewsRssScraper, "fetch", autospec=True, return_value=[{
                    "title": "新闻测试",
                    "content": "这是一段新闻素材",
                    "source": "新闻RSS",
                    "category": "news",
                }]) as fetch:
                    worker.run()

        fetch.assert_called_once()
        self.assertEqual(len(fetch.call_args.args), 1)
        self.assertEqual(errors, [])
        self.assertEqual(finished, [1])
        self.assertTrue(conn.closed)

    def test_material_download_worker_reports_empty_fetch_as_error(self):
        ensure_qt_app()
        from unittest.mock import Mock, patch
        from src.materials.scrapers.idiom_fetcher import IdiomFetcher
        from src.ui.screens.material_screen import DownloadWorker

        class DummyConn:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        conn = DummyConn()
        app_stub = Mock()
        app_stub.db.create_thread_connection.return_value = conn
        worker = DownloadWorker("idiom", count=50)
        errors = []
        finished = []
        worker.error.connect(errors.append)
        worker.finished.connect(finished.append)

        with patch("src.app.App.instance", return_value=app_stub):
            with patch("src.ui.screens.material_screen.MaterialStore"):
                with patch.object(IdiomFetcher, "fetch", autospec=True, return_value=[]):
                    worker.run()

        self.assertEqual(finished, [])
        self.assertTrue(errors)
        self.assertIn("未获取到素材", errors[0])
        self.assertTrue(conn.closed)

    def test_idiom_fetcher_uses_builtin_data_without_network(self):
        from unittest.mock import patch
        from src.materials.scrapers.idiom_fetcher import IdiomFetcher

        with patch.object(
            IdiomFetcher,
            "_throttled_get",
            autospec=True,
            side_effect=AssertionError("network should not be used"),
        ) as get:
            materials = IdiomFetcher().fetch()

        self.assertEqual(get.call_count, 0)
        self.assertGreater(len(materials), 0)
        self.assertEqual(materials[0]["source"], "成语数据集")
        self.assertEqual(materials[0]["category"], "idiom")

    def test_news_rss_scraper_uses_peoples_daily_rss(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.materials.scrapers.news_rss import NewsRssScraper

        feed = SimpleNamespace(entries=[
            SimpleNamespace(title="人民网新闻", summary="<p>人民网新闻正文内容用于测试</p>"),
        ])
        response = SimpleNamespace(text="<rss></rss>")

        with patch.object(NewsRssScraper, "_throttled_get", autospec=True, return_value=response) as get:
            with patch("src.materials.scrapers.news_rss.feedparser.parse", return_value=feed):
                materials = NewsRssScraper().fetch()

        self.assertEqual(get.call_args.args[1], "http://www.people.com.cn/rss/ywkx.xml")
        self.assertEqual(len(materials), 1)
        self.assertEqual(materials[0]["title"], "人民网新闻")
        self.assertEqual(materials[0]["content"], "人民网新闻正文内容用于测试")
        self.assertEqual(materials[0]["source"], "新闻RSS")

    def test_news_rss_scraper_uses_title_when_feed_has_no_summary(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from src.materials.scrapers.news_rss import NewsRssScraper

        title = "人民网新闻标题可以作为短素材"
        feed = SimpleNamespace(entries=[
            SimpleNamespace(title=title),
        ])
        response = SimpleNamespace(text="<rss></rss>", encoding="")

        with patch.object(NewsRssScraper, "_throttled_get", autospec=True, return_value=response):
            with patch("src.materials.scrapers.news_rss.feedparser.parse", return_value=feed):
                materials = NewsRssScraper().fetch()

        self.assertEqual(len(materials), 1)
        self.assertEqual(materials[0]["content"], title)
        self.assertEqual(materials[0]["category"], "news")

    def test_legal_scraper_uses_flk_source(self):
        from unittest.mock import patch
        from src.materials.scrapers.legal_scraper import LegalScraper

        response = type("Resp", (), {
            "text": """
                <html><body>
                    <div class=\"item\"><a href=\"/detail?id=1\">中华人民共和国刑法</a></div>
                </body></html>
            """
        })()

        with patch.object(LegalScraper, "_throttled_get", autospec=True, return_value=response) as get:
            materials = LegalScraper().fetch()

        self.assertEqual(get.call_args.args[1], "https://flk.npc.gov.cn/")
        self.assertEqual(len(materials), 1)
        self.assertEqual(materials[0]["title"], "中华人民共和国刑法")
        self.assertEqual(materials[0]["source"], "法律法规")

    def test_legal_scraper_falls_back_to_builtin_when_online_empty(self):
        from unittest.mock import patch
        from src.materials.scrapers.legal_scraper import LegalScraper

        response = type("Resp", (), {"text": "<html><body><div id=\"app\"></div></body></html>"})()

        with patch.object(LegalScraper, "_throttled_get", autospec=True, return_value=response):
            materials = LegalScraper().fetch()

        self.assertGreater(len(materials), 0)
        self.assertEqual(materials[0]["category"], "legal")
        self.assertEqual(materials[0]["source"], "法律法规")

    def test_poetry_scraper_uses_reachable_gushiwen_source(self):
        from unittest.mock import patch
        from src.materials.scrapers.gushiwen import GushiwenScraper

        response = type("Resp", (), {
            "text": """
                <html><body>
                    <div class="sons">
                        <div class="cont">
                            <b>蝇</b>
                            <div class="contson">乘炎出何许，人意以微看。<br/>怒剑休追逐，疑屏漫指弹。</div>
                        </div>
                    </div>
                </body></html>
            """
        })()

        with patch.object(GushiwenScraper, "_throttled_get", autospec=True, return_value=response) as get:
            materials = GushiwenScraper().fetch()

        self.assertEqual(get.call_args.args[1], "https://www.gushiwen.cn/")
        self.assertEqual(len(materials), 1)
        self.assertEqual(materials[0]["title"], "蝇")
        self.assertEqual(materials[0]["source"], "古诗文网")


if __name__ == "__main__":
    unittest.main()
