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


if __name__ == "__main__":
    unittest.main()
