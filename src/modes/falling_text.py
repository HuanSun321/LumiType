import time
import random
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPainter
from src.materials.material_manager import MaterialManager
from src.ui.widgets.falling_item import FallingCharItem
from src.modes.base_mode import BaseTypingMode


class FallingTextMode(BaseTypingMode):
    """Characters fall from top; type their pinyin (English) to eliminate them."""

    MAX_LIVES = 5
    MAX_ON_SCREEN = 25
    DANGER_ZONE_Y = 0.95
    SCENE_WIDTH = 800
    SCENE_HEIGHT = 600
    MAX_FALL_SPEED = 200

    def __init__(self, difficulty: int = 3, category: str = None, ratio: float = 1.0):
        super().__init__()
        self._difficulty = difficulty
        self._category = category
        self._ratio = ratio
        self._materials = MaterialManager.instance().get_materials(category=category)
        self._char_pool = self._build_char_pool()
        self._pinyin_map = self._build_pinyin_map()
        self._font = QFont("Microsoft YaHei", 22)

        # Pinyin accumulator
        self._current_pinyin = ""

        # Game state
        self._lives = self.MAX_LIVES

        # Falling items
        self._items: set[FallingCharItem] = set()
        self._target_item: FallingCharItem | None = None

        # Spawn control
        self._spawn_interval = self._base_spawn_interval()
        self._last_spawn = 0.0
        self._fall_speed = self._base_fall_speed()

        # Scene/view (created lazily)
        self._scene: QGraphicsScene | None = None
        self._view: QGraphicsView | None = None
        self._container: QWidget | None = None

    def _build_char_pool(self) -> list[str]:
        chars = set()
        for m in self._materials:
            for ch in m.get("content", ""):
                if self._is_cjk(ch):
                    chars.add(ch)
        return list(chars) if chars else list("天地人和风雨山水花鸟鱼虫")

    def _is_cjk(self, ch: str) -> bool:
        cp = ord(ch)
        return (0x4E00 <= cp <= 0x9FFF or
                0x3400 <= cp <= 0x4DBF or
                0x20000 <= cp <= 0x2A6DF)

    def _build_pinyin_map(self) -> dict[str, list[str]]:
        """Build char → list of all pinyin readings."""
        mapping: dict[str, list[str]] = {}
        try:
            from pypinyin import pinyin, Style
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

    @property
    def lives(self) -> int:
        return self._lives

    @property
    def current_pinyin(self) -> str:
        return self._current_pinyin

    @property
    def material(self) -> dict:
        return {"title": "掉落消除", "category": "falling"}

    def setup(self, engine):
        super().setup(engine)
        self._last_spawn = time.time()
        # Fit scene to viewport once widget is shown
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._fit_scene_to_viewport)

    def teardown(self):
        self._items.clear()
        self._target_item = None
        self._current_pinyin = ""

    def get_widget(self) -> QWidget:
        if self._container is None:
            self._container = QWidget()
            layout = QVBoxLayout(self._container)
            layout.setContentsMargins(0, 0, 0, 0)

            self._scene = QGraphicsScene(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
            self._view = QGraphicsView(self._scene)
            self._view.setStyleSheet("background: transparent; border: none;")
            self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            layout.addWidget(self._view)

        return self._container

    def _fit_scene_to_viewport(self):
        """Scale scene so full height is visible, draw danger zone line."""
        if not self._view:
            return
        vw = self._view.viewport().width()
        vh = self._view.viewport().height()
        if vw <= 0 or vh <= 0:
            return
        scale = vh / self.SCENE_HEIGHT
        from PyQt6.QtGui import QTransform
        self._view.setTransform(QTransform().scale(scale, scale))
        self._view.setSceneRect(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
        self._draw_danger_line()

    def _draw_danger_line(self):
        """Draw a dashed red line at the danger zone so the player can see it."""
        if not self._scene:
            return
        # Remove old danger line items
        for it in list(self._scene.items()):
            if getattr(it, '_is_danger_line', False):
                self._scene.removeItem(it)
        from PyQt6.QtWidgets import QGraphicsLineItem
        from PyQt6.QtGui import QPen, QColor
        from PyQt6.QtCore import Qt
        danger_y = self.SCENE_HEIGHT * 0.95
        line = QGraphicsLineItem(0, danger_y, self.SCENE_WIDTH, danger_y)
        pen = QPen(QColor(255, 100, 100, 150), 2, Qt.PenStyle.DashLine)
        line.setPen(pen)
        line._is_danger_line = True
        line.setZValue(-1)
        self._scene.addItem(line)

    def process_input(self, text: str):
        """In direct mode, each character is an English letter. Accumulate pinyin."""
        for ch in text:
            ch = ch.lower()
            if not ch.isalpha():
                # Non-alpha key (space, backspace etc) — reset pinyin
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
                    self._retarget()
            elif len(self._current_pinyin) > 8:
                # Too long without match — reset to avoid stuck state
                self._current_pinyin = ""

        # Highlight best prefix match
        self._update_preview()

    def process_composing(self, pinyin: str):
        """Not used in direct mode."""
        pass

    def _find_pinyin_match(self, pinyin: str) -> FallingCharItem | None:
        """Find lowest on-screen item whose pinyin equals the given string."""
        best = None
        best_y = -1
        for item in self._items:
            if item.state == FallingCharItem.STATE_ELIMINATED:
                continue
            readings = self._pinyin_map.get(item.char, [])
            if pinyin in readings and item.pos().y() > best_y:
                best = item
                best_y = item.pos().y()
        return best

    def _update_preview(self):
        """Highlight the lowest item matching the current pinyin prefix."""
        if not self._current_pinyin:
            self._retarget()
            return
        match = self._find_prefix_match(self._current_pinyin)
        if match:
            if match is not self._target_item:
                self._retarget_to(match)
        else:
            self._retarget()

    def _find_prefix_match(self, prefix: str) -> FallingCharItem | None:
        """Find lowest item with any pinyin starting with prefix."""
        best = None
        best_y = -1
        for item in self._items:
            if item.state == FallingCharItem.STATE_ELIMINATED:
                continue
            readings = self._pinyin_map.get(item.char, [])
            if any(r.startswith(prefix) for r in readings) and item.pos().y() > best_y:
                best = item
                best_y = item.pos().y()
        return best

    def _retarget(self):
        """Set the lowest active item as target. Clear ALL other items' targeted state."""
        best = self._find_lowest_active()
        if best is self._target_item:
            return  # no change needed
        # Clear ALL targeted states first
        for item in self._items:
            if item.state == FallingCharItem.STATE_TARGETED and item is not best:
                item.set_falling()
        self._target_item = best
        if best:
            best.set_targeted()

    def _retarget_to(self, item: FallingCharItem):
        """Manually target a specific item."""
        if self._target_item and self._target_item is not item:
            self._target_item.set_falling()
        self._target_item = item
        item.set_targeted()

    def _find_lowest_active(self) -> FallingCharItem | None:
        best = None
        best_y = -1
        for item in self._items:
            if item.state not in (FallingCharItem.STATE_FALLING, FallingCharItem.STATE_TARGETED):
                continue
            if item.pos().y() > best_y:
                best = item
                best_y = item.pos().y()
        return best

    def on_tick(self):
        """Called every 16ms for animation."""
        if not self._scene:
            return

        now = time.time()
        dt = 0.016

        if now - self._last_spawn >= self._spawn_interval:
            self._spawn_item()
            self._last_spawn = now
            elapsed = now - self._start_time
            self._spawn_interval = max(0.3, self._base_spawn_interval() - elapsed * 0.005)
            self._fall_speed = min(self._base_fall_speed() + elapsed * 1.5, self.MAX_FALL_SPEED)

        # Danger zone: 95% of visible viewport height, converted to scene coords
        if self._view and self._view.viewport().height() > 0:
            from PyQt6.QtCore import QPoint
            vp_y = int(self._view.viewport().height() * 0.95)
            danger_y = self._view.mapToScene(QPoint(0, vp_y)).y()
        else:
            danger_y = self.SCENE_HEIGHT * 0.95

        to_remove = set()
        for item in list(self._items):
            alive = item.advance(dt)
            if not alive:
                to_remove.add(item)
            elif item.state != FallingCharItem.STATE_ELIMINATED:
                if item.pos().y() >= danger_y:
                    # Crossed danger line —扣血 once, then eliminate immediately
                    self._lives -= 1
                    item.eliminate()
                    if self._target_item is item:
                        self._target_item = None
                    if self._lives <= 0 and self._engine:
                        self._engine.end()

        self._items -= to_remove
        for item in to_remove:
            if self._scene:
                self._scene.removeItem(item)

        self._retarget()

    def on_logic(self):
        pass

    def _spawn_item(self):
        if not self._scene or len(self._items) >= self.MAX_ON_SCREEN:
            return
        if not self._char_pool:
            return

        char = random.choice(self._char_pool)
        # Use scene coordinates for spawn position, clamped to visible area
        if self._view and self._view.viewport().width() > 0:
            # Convert viewport edges to scene coords to get visible x range
            from PyQt6.QtCore import QPoint
            left_scene = self._view.mapToScene(QPoint(0, 0)).x()
            right_scene = self._view.mapToScene(QPoint(self._view.viewport().width(), 0)).x()
            x_min = max(10, left_scene + 20)
            x_max = min(self.SCENE_WIDTH - 60, right_scene - 60)
        else:
            x_min = 20
            x_max = self.SCENE_WIDTH - 60
        if x_max <= x_min:
            x_max = x_min + 40
        x = random.randint(int(x_min), int(x_max))
        y = -50

        readings = self._pinyin_map.get(char, [""])
        pinyin_hint = readings[0] if readings else ""
        item = FallingCharItem(char, x, y, self._fall_speed, self._font,
                               pinyin=pinyin_hint)
        item.eliminated.connect(lambda it=item: self._on_item_eliminated(it), Qt.ConnectionType.QueuedConnection)
        self._scene.addItem(item)
        self._items.add(item)

    def _on_item_eliminated(self, item: FallingCharItem):
        self._items.discard(item)
        if self._scene:
            self._scene.removeItem(item)
        if self._target_item is item:
            self._target_item = None

    def calculate_result(self) -> dict:
        return self._base_result("falling", "掉落消除")
