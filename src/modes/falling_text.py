"""Falling text mode: characters fall from the top, type them before they reach the bottom."""
import random

from PyQt6.QtCore import QPoint, QTimer, Qt
from PyQt6.QtGui import QFont, QPainter, QTransform
from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget
from src.core.game_state import GameMode
from src.materials.material_manager import MaterialManager
from src.modes.base_mode import BaseTypingMode
from src.constants import (
    MAX_LIVES, MAX_ON_SCREEN, DANGER_ZONE_Y,
    SCENE_WIDTH, SCENE_HEIGHT, MAX_FALL_SPEED,
)
from src.ui.widgets.falling_item import FallingCharItem


class FallingItem:
    """A single falling character on the game scene."""

    def __init__(self, char: str, x: float, speed: float):
        self.char: str = char
        self.x: float = x
        self.y: float = 0.0
        self.speed: float = speed
        self.typed: bool = False
        self.missed: bool = False

    def update(self, dt: float) -> None:
        self.y += self.speed * dt


class FallingTextMode(BaseTypingMode):
    mode = GameMode.FALLING_TEXT

    def __init__(self, difficulty: int = 3, category: str = None, ratio: float = 1.0):
        super().__init__()
        self._difficulty = difficulty
        self._category = category
        self._ratio = ratio
        self._materials = MaterialManager.instance().get_materials(category=category)
        self._char_pool = self._build_char_pool()
        self._pinyin_map = self._build_pinyin_map()
        self.set_text("".join(self._char_pool))
        self._items: set[FallingCharItem] = set()
        self._target_item: FallingCharItem | None = None
        self._lives: int = MAX_LIVES
        self._spawn_timer: float = 0.0
        self._spawn_interval: float = self._base_spawn_interval()
        self._fall_speed: float = self._base_fall_speed()
        self._current_pinyin = ""
        self._font = QFont("Microsoft YaHei", 22)
        self._scene: QGraphicsScene | None = None
        self._view: QGraphicsView | None = None
        self._container: QWidget | None = None

    @property
    def lives(self) -> int:
        return self._lives

    @property
    def items(self) -> set[FallingCharItem]:
        return self._items

    @property
    def material(self) -> dict:
        return {"title": "掉落消除", "category": "falling", "content": self._text}

    @property
    def current_cpm(self) -> float:
        from src.core.statistics import StatsCalculator
        return StatsCalculator.rolling_cpm(self._recent_chars)

    @property
    def current_accuracy(self) -> float:
        from src.core.statistics import StatsCalculator
        return StatsCalculator.accuracy(self._correct_count, self._total_typed)

    def start(self) -> None:
        self.teardown()
        self._lives = MAX_LIVES
        self._spawn_timer = 0.0
        self._spawn_interval = self._base_spawn_interval()
        self._fall_speed = self._base_fall_speed()
        self._current_pinyin = ""
        QTimer.singleShot(0, self._fit_scene_to_viewport)

    def teardown(self):
        if self._scene:
            for item in list(self._items):
                self._scene.removeItem(item)
        self._items.clear()
        self._target_item = None

    def get_widget(self) -> QWidget:
        if self._container is None:
            self._container = QWidget()
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)

            self._scene = QGraphicsScene(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
            self._view = QGraphicsView(self._scene)
            self._view.setStyleSheet("background: transparent; border: none;")
            self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            layout.addWidget(self._view)
            self._draw_danger_line()
        return self._container

    def process_input(self, typed: str) -> dict:
        if not typed:
            return {"hit": False, "score": 0}

        hit = False
        for ch in typed:
            ch = ch.lower()
            if not ch.isalpha():
                self._current_pinyin = ""
                continue
            self._current_pinyin += ch
            matched = self._find_pinyin_match(self._current_pinyin)
            if matched:
                self._record_char(True)
                matched.eliminate()
                self._current_pinyin = ""
                if self._target_item is matched:
                    self._target_item = None
                hit = True
            elif len(self._current_pinyin) > 8:
                expected = self._target_item.char if self._target_item else ""
                self._record_mistake(expected, self._current_pinyin, self._total_typed)
                self._record_char(False)
                self._current_pinyin = ""
        self._update_preview()
        return {"hit": hit, "score": self._engine.scoring.score if self._engine else 0}

    def on_tick(self, dt: float = 0.016) -> None:
        # Spawn new items
        self._spawn_timer += dt
        if self._spawn_timer >= self._spawn_interval and len(self._items) < MAX_ON_SCREEN:
            self._spawn_item()
            self._spawn_timer = 0.0

        danger_y = self._danger_y()
        to_remove: set[FallingCharItem] = set()
        for item in list(self._items):
            alive = item.advance(dt)
            if not alive:
                to_remove.add(item)
            elif item.state != FallingCharItem.STATE_ELIMINATED and item.pos().y() >= danger_y:
                item.eliminate()
                to_remove.add(item)
                self._record_mistake(item.char, "", self._total_typed)
                self._record_char(False)
                if self._target_item is item:
                    self._target_item = None
                if self._lives > 0:
                    self._lives -= 1

        for item in to_remove:
            self._items.discard(item)
            if self._scene:
                self._scene.removeItem(item)

        # Increase difficulty over time
        elapsed = max(0.0, self._engine.elapsed_seconds if self._engine else 0.0)
        self._spawn_interval = max(0.3, self._base_spawn_interval() - elapsed * 0.005)
        self._fall_speed = min(self._base_fall_speed() + elapsed * 1.5, MAX_FALL_SPEED)
        self._retarget()

        if self.is_game_over() and self._engine:
            self._engine.end()

    def _spawn_item(self) -> None:
        if not self._scene or not self._char_pool:
            return
        char = random.choice(self._char_pool)
        x = random.uniform(30, SCENE_WIDTH - 80)
        readings = self._pinyin_map.get(char, [""])
        pinyin_hint = readings[0] if readings else ""
        item = FallingCharItem(char, x, -50, self._fall_speed, self._font, pinyin=pinyin_hint)
        self._scene.addItem(item)
        self._items.add(item)

    def is_game_over(self) -> bool:
        return self._lives <= 0

    def get_result(self) -> dict:
        return {
            "mode": "falling",
            "total_chars": self._total_typed,
            "correct_chars": self._correct_count,
            "accuracy": self.current_accuracy,
            "cpm": self.current_cpm,
            "lives_remaining": self._lives,
            "material_title": "掉落消除",
        }

    def _build_char_pool(self) -> list[str]:
        chars = set()
        for m in self._materials:
            for ch in m.get("content", ""):
                if self._is_cjk(ch):
                    chars.add(ch)
        return list(chars) if chars else list("天地人和风雨山水花鸟鱼虫")

    def _build_pinyin_map(self) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        try:
            from pypinyin import Style, pinyin
            for ch in self._char_pool:
                py_list = pinyin(ch, style=Style.NORMAL, heteronym=True)
                if py_list and py_list[0]:
                    mapping[ch] = py_list[0]
        except ImportError:
            pass
        return mapping

    def _base_spawn_interval(self) -> float:
        return max(0.4, 2.0 - (self._difficulty - 1) * 0.3)

    def _base_fall_speed(self) -> float:
        return 40 + (self._difficulty - 1) * 15

    def _is_cjk(self, ch: str) -> bool:
        cp = ord(ch)
        return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF

    def _find_pinyin_match(self, value: str) -> FallingCharItem | None:
        best = None
        best_y = -1.0
        for item in self._items:
            if item.state == FallingCharItem.STATE_ELIMINATED:
                continue
            if value in self._pinyin_map.get(item.char, []) and item.pos().y() > best_y:
                best = item
                best_y = item.pos().y()
        return best

    def _find_prefix_match(self, prefix: str) -> FallingCharItem | None:
        best = None
        best_y = -1.0
        for item in self._items:
            if item.state == FallingCharItem.STATE_ELIMINATED:
                continue
            readings = self._pinyin_map.get(item.char, [])
            if any(r.startswith(prefix) for r in readings) and item.pos().y() > best_y:
                best = item
                best_y = item.pos().y()
        return best

    def _update_preview(self):
        match = self._find_prefix_match(self._current_pinyin) if self._current_pinyin else None
        if match:
            self._retarget_to(match)
        else:
            self._retarget()

    def _retarget(self):
        best = None
        best_y = -1.0
        for item in self._items:
            if item.state not in (FallingCharItem.STATE_FALLING, FallingCharItem.STATE_TARGETED):
                continue
            if item.pos().y() > best_y:
                best = item
                best_y = item.pos().y()
        if best is self._target_item:
            return
        for item in self._items:
            if item.state == FallingCharItem.STATE_TARGETED:
                item.set_falling()
        self._target_item = best
        if best:
            best.set_targeted()

    def _retarget_to(self, item: FallingCharItem):
        if self._target_item and self._target_item is not item:
            self._target_item.set_falling()
        self._target_item = item
        item.set_targeted()

    def _fit_scene_to_viewport(self):
        if not self._view:
            return
        viewport = self._view.viewport()
        if viewport.width() <= 0 or viewport.height() <= 0:
            return
        scale = viewport.height() / SCENE_HEIGHT
        self._view.setTransform(QTransform().scale(scale, scale))
        self._view.setSceneRect(0, 0, SCENE_WIDTH, SCENE_HEIGHT)
        self._draw_danger_line()

    def _draw_danger_line(self):
        if not self._scene:
            return
        for item in list(self._scene.items()):
            if getattr(item, "_is_danger_line", False):
                self._scene.removeItem(item)
        danger_y = SCENE_HEIGHT * DANGER_ZONE_Y
        line = QGraphicsLineItem(0, danger_y, SCENE_WIDTH, danger_y)
        from PyQt6.QtGui import QColor, QPen
        line.setPen(QPen(QColor(255, 100, 100, 150), 2, Qt.PenStyle.DashLine))
        line._is_danger_line = True
        line.setZValue(-1)
        self._scene.addItem(line)

    def _danger_y(self) -> float:
        if self._view and self._view.viewport().height() > 0:
            vp_y = int(self._view.viewport().height() * DANGER_ZONE_Y)
            return self._view.mapToScene(QPoint(0, vp_y)).y()
        return SCENE_HEIGHT * DANGER_ZONE_Y
