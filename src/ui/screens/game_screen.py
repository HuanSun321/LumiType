from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from src.core.game_state import GameMode
from src.core.game_engine import GameEngine
from src.modes.follow_typing import FollowTypingMode
from src.modes.falling_text import FallingTextMode
from src.modes.timed_challenge import TimedChallengeMode
from src.ui.widgets.input_bar import InputBar
from src.ui.widgets.text_display import TextDisplayWidget
from src.ui.widgets.combo_display import ComboDisplay
from src.ui.widgets.progress_ring import ProgressRing
from src.constants import (
    COLOR_PINK_LIGHT, COLOR_ACCENT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH, COLOR_SKY, COLOR_HIGHLIGHT, COLOR_ERROR,
)
from src.app import App


_HUD_LABEL_STYLE = f"""
    font-size: 16px;
    font-weight: bold;
    color: #5B4A4A;
    background-color: {COLOR_CREAM};
    border: 2px dashed {COLOR_PINK_LIGHT};
    border-radius: 12px;
    padding: 4px 12px;
"""

_HUD_LABEL_ACCENT = f"""
    font-size: 16px;
    font-weight: bold;
    color: {COLOR_ACCENT};
    background-color: {COLOR_CREAM};
    border: 2px dashed {COLOR_PINK_LIGHT};
    border-radius: 12px;
    padding: 4px 12px;
"""


def _make_hud_label(text: str, style: str = _HUD_LABEL_STYLE) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    return lbl


class GameScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()
        self._engine = GameEngine()
        self._mode = None
        self._mode_name = ""
        self._input_bar = None
        self._display = None
        self._falling_widget = None
        self._combo_display = None
        self._progress_ring = None
        self._timer_label = None
        self._lives_label = None
        self._top_bar = None
        self._hud_timer = QTimer(self)
        self._hud_timer.setInterval(200)
        self._hud_timer.timeout.connect(self._update_hud)

        self._engine.game_over.connect(self._on_game_over)
        self._engine.state_changed.connect(self._on_state_changed)

    def on_enter(self, data: dict):
        mode_name = data.get("mode", GameMode.FOLLOW_TYPING.value)
        self._mode_name = mode_name
        self._category = data.get("category")
        self._ratio = data.get("ratio", 1.0)
        self._setup_mode(mode_name)

    def _setup_mode(self, mode_name: str):
        self._engine.cleanup()
        self._hud_timer.stop()

        self._falling_widget = None
        self._display = None

        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
        else:
            layout = QVBoxLayout(self)

        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 16)

        # Top bar (HUD)
        self._top_bar = self._create_top_bar(mode_name)
        layout.addWidget(self._top_bar)

        # Mode-specific setup
        if mode_name == GameMode.FALLING_TEXT.value:
            self._mode = FallingTextMode(category=self._category, ratio=self._ratio)
            self._falling_widget = self._mode.get_widget()
            self._falling_widget.setStyleSheet(f"""
                background-color: {COLOR_SKY};
                border: 2px dashed {COLOR_PINK_LIGHT};
                border-radius: 16px;
            """)
            layout.addWidget(self._falling_widget, stretch=1)
        elif mode_name == GameMode.TIMED_CHALLENGE.value:
            self._mode = TimedChallengeMode(category=self._category, ratio=self._ratio)
            self._display = TextDisplayWidget()
            self._display.setStyleSheet(f"""
                background-color: {COLOR_CREAM};
                border: 2px dashed {COLOR_PINK_LIGHT};
                border-radius: 16px;
            """)
            layout.addWidget(self._display, stretch=1)
        else:
            self._mode = FollowTypingMode(category=self._category, ratio=self._ratio)
            self._display = TextDisplayWidget()
            self._display.setStyleSheet(f"""
                background-color: {COLOR_CREAM};
                border: 2px dashed {COLOR_PINK_LIGHT};
                border-radius: 16px;
            """)
            layout.addWidget(self._display, stretch=1)

        # Combo display
        self._combo_display = ComboDisplay()
        layout.addWidget(self._combo_display)

        # Input bar
        self._input_bar = InputBar()
        self._input_bar.text_committed.connect(self._on_input)
        self._input_bar.composing_changed.connect(self._on_composing)
        if mode_name == GameMode.FALLING_TEXT.value:
            self._input_bar.set_direct_mode(True)
        layout.addWidget(self._input_bar)

        # Pinyin display for falling text mode
        self._pinyin_display = None
        if mode_name == GameMode.FALLING_TEXT.value:
            self._pinyin_display = QLabel("")
            self._pinyin_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._pinyin_display.setStyleSheet(f"""
                font-size: 20px;
                font-weight: bold;
                color: {COLOR_ACCENT};
                background-color: {COLOR_CREAM};
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 12px;
                padding: 4px 16px;
                min-height: 24px;
            """)
            layout.addWidget(self._pinyin_display)

        # Initialize display content
        if self._display and hasattr(self._mode, 'material'):
            self._display.set_material(self._mode.material)

        # Guard: skip start if text is empty
        if hasattr(self._mode, '_text') and not self._mode._text:
            return

        self._engine.start(self._mode)
        self._input_bar.setFocus()
        self._hud_timer.start()

    def _create_top_bar(self, mode_name: str) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(f"""
            background-color: {COLOR_LAVENDER};
            border: 2px dashed {COLOR_PINK_LIGHT};
            border-radius: 14px;
            padding: 4px;
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 6, 12, 6)
        bar_layout.setSpacing(10)

        self._score_label = _make_hud_label("✨ 0")
        bar_layout.addWidget(self._score_label)

        self._combo_label = _make_hud_label("🔗 0")
        bar_layout.addWidget(self._combo_label)

        self._cpm_label = _make_hud_label("⚡ 0")
        bar_layout.addWidget(self._cpm_label)

        self._accuracy_label = _make_hud_label("🎯 100%")
        bar_layout.addWidget(self._accuracy_label)

        # Mode-specific HUD
        if mode_name == GameMode.FALLING_TEXT.value:
            self._lives_label = _make_hud_label("💖 × 5", _HUD_LABEL_ACCENT)
            bar_layout.addWidget(self._lives_label)
            self._timer_label = None
            self._progress_ring = None
        elif mode_name == GameMode.TIMED_CHALLENGE.value:
            self._progress_ring = ProgressRing()
            self._progress_ring.setFixedSize(48, 48)
            bar_layout.addWidget(self._progress_ring)
            self._timer_label = _make_hud_label("⏰ 120s", _HUD_LABEL_ACCENT)
            bar_layout.addWidget(self._timer_label)
            self._lives_label = None
        else:
            self._timer_label = None
            self._progress_ring = None
            self._lives_label = None

        bar_layout.addStretch()

        self._multiplier_label = _make_hud_label("1.0x", _HUD_LABEL_ACCENT)
        bar_layout.addWidget(self._multiplier_label)

        self._pause_btn = QPushButton("⏸ 暂停")
        self._pause_btn.setFixedWidth(90)
        self._pause_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_PEACH};
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
            }}
        """)
        self._pause_btn.clicked.connect(self._toggle_pause)
        bar_layout.addWidget(self._pause_btn)

        self._quit_btn = QPushButton("🚪 退出")
        self._quit_btn.setFixedWidth(80)
        self._quit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFE0E0;
                color: #5B4A4A;
                border: 2px solid {COLOR_PINK_LIGHT};
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ERROR};
                color: #ffffff;
            }}
        """)
        self._quit_btn.clicked.connect(self._quit_to_menu)
        self._quit_btn.setVisible(False)
        bar_layout.addWidget(self._quit_btn)

        return bar

    def _on_input(self, text: str):
        prev_score = self._engine.scoring.score
        prev_combo = self._engine.scoring.combo
        self._engine.process_input(text)
        self._update_display()
        self._update_hud()

        # Sound effects
        sound = App.instance().sound
        new_score = self._engine.scoring.score
        new_combo = self._engine.scoring.combo
        if new_score > prev_score:
            sound.play("correct")
        elif new_combo == 0 and prev_combo > 0:
            sound.play("wrong")
        else:
            sound.play("click")
        if new_combo > 0 and new_combo % 10 == 0 and new_combo > prev_combo:
            sound.play("combo")

    def _on_composing(self, pinyin: str):
        if (self._mode
                and self._mode_name == GameMode.FALLING_TEXT.value
                and hasattr(self._mode, 'process_composing')):
            self._mode.process_composing(pinyin)
            self._update_display()
            self._update_hud()

    def _update_display(self):
        if not self._mode:
            return

        if self._mode_name == GameMode.FALLING_TEXT.value:
            pass
        elif self._display:
            self._display.set_cursor_position(self._mode.cursor_position)
            self._display.set_char_states(self._mode.char_states)

            if self._mode_name == GameMode.TIMED_CHALLENGE.value:
                current_title = self._mode.material.get("title", "")
                if current_title != getattr(self._display, 'title', ''):
                    self._display.set_material(self._mode.material)

    def _update_hud(self):
        if not self._mode:
            return

        scoring = self._engine.scoring
        self._score_label.setText(f"✨ {scoring.score}")
        self._combo_label.setText(f"🔗 {scoring.combo}")
        self._multiplier_label.setText(f"×{scoring.multiplier:.1f}")

        cpm = self._mode.current_cpm
        self._cpm_label.setText(f"⚡ {cpm:.0f}")
        acc = self._mode.current_accuracy
        self._accuracy_label.setText(f"🎯 {acc:.0%}")

        if scoring.combo >= 10:
            self._combo_display.show_combo(scoring.combo, scoring.multiplier)

        if self._pinyin_display and hasattr(self._mode, 'current_pinyin'):
            py = self._mode.current_pinyin
            self._pinyin_display.setText(f"拼音: {py}_" if py else "")

        if self._lives_label and hasattr(self._mode, 'lives'):
            lives = self._mode.lives
            hearts = "💖" * lives + "🤍" * max(0, 5 - lives)
            self._lives_label.setText(hearts)
            if lives <= 2:
                self._lives_label.setStyleSheet(_HUD_LABEL_ACCENT.replace(COLOR_CREAM, "#FFE0E0"))
            else:
                self._lives_label.setStyleSheet(_HUD_LABEL_ACCENT)

        if self._timer_label and hasattr(self._mode, 'time_remaining'):
            remaining = self._mode.time_remaining
            self._timer_label.setText(f"⏰ {remaining}s")
            if remaining <= 10:
                self._timer_label.setStyleSheet(_HUD_LABEL_ACCENT.replace(COLOR_CREAM, "#FFE0E0"))
            else:
                self._timer_label.setStyleSheet(_HUD_LABEL_ACCENT)

        if self._progress_ring and hasattr(self._mode, 'time_remaining'):
            total = self._mode.duration
            remaining = self._mode.time_remaining
            self._progress_ring.set_progress(remaining / total if total > 0 else 0)

    def _toggle_pause(self):
        if self._engine.state.value == "playing":
            self._engine.pause()
            self._hud_timer.stop()
            self._pause_btn.setText("▶ 继续")
            self._quit_btn.setVisible(True)
        elif self._engine.state.value == "paused":
            self._engine.resume()
            self._hud_timer.start()
            self._input_bar.setFocus()
            self._pause_btn.setText("⏸ 暂停")
            self._quit_btn.setVisible(False)

    def _quit_to_menu(self):
        self._engine.cleanup()
        self._hud_timer.stop()
        if self.navigate_to:
            self.navigate_to("menu")

    def _on_state_changed(self, state):
        if state.value == "ended":
            self._input_bar.setEnabled(False)
            self._hud_timer.stop()

    def _on_game_over(self, result: dict):
        self._hud_timer.stop()
        App.instance().sound.play("game_over")
        result["mode"] = self._mode_name
        self._save_result(result)
        if self.navigate_to:
            self.navigate_to("results", result)

    def _save_result(self, result: dict):
        from src.app import App
        from datetime import datetime
        try:
            db = App.instance().db
            db.conn.execute("""
                INSERT INTO game_results
                (mode, played_at, duration_seconds, total_chars, correct_chars,
                 accuracy, cpm, score, max_combo, difficulty, material_source, material_title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.get("mode", ""),
                datetime.now().isoformat(),
                int(result.get("elapsed", 0)),
                result.get("total_chars", 0),
                result.get("correct_chars", 0),
                result.get("accuracy", 0),
                result.get("cpm", 0),
                result.get("score", 0),
                result.get("max_combo", 0),
                result.get("difficulty", 1),
                result.get("material_source", ""),
                result.get("material_title", ""),
            ))
            db.conn.commit()
        except Exception as e:
            print(f"Failed to save result: {e}")
