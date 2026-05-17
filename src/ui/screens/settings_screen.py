from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QCheckBox, QSpinBox, QGroupBox, QFormLayout,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt
from src.app import App
from src.constants import (
    COLOR_ACCENT, COLOR_PINK_LIGHT, COLOR_LAVENDER, COLOR_MINT,
    COLOR_CREAM, COLOR_PEACH,
)


_GROUP_STYLE = f"""
    QGroupBox {{
        font-size: 16px;
        font-weight: bold;
        color: {COLOR_ACCENT};
        border: 2px dashed {COLOR_PINK_LIGHT};
        border-radius: 16px;
        margin-top: 14px;
        padding-top: 22px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
    }}
"""


class SettingsScreen(QWidget):
    navigate_to = None

    def __init__(self):
        super().__init__()
        self._config = App.instance().config
        self._built = False

    def on_enter(self, data: dict):
        if not self._built:
            self._build_ui()
            self._built = True

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        main_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(36, 24, 36, 24)

        # Header
        header = QHBoxLayout()
        back_btn = QPushButton("← 返回")
        back_btn.setObjectName("back_btn")
        back_btn.setFixedWidth(100)
        back_btn.clicked.connect(lambda: self.navigate_to("menu") if self.navigate_to else None)
        header.addWidget(back_btn)
        header.addStretch()
        title = QLabel("⚙️ 设置")
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLOR_ACCENT};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Font settings
        font_group = QGroupBox("✏️ 字体设置")
        font_group.setStyleSheet(_GROUP_STYLE)
        font_layout = QFormLayout()
        font_layout.setSpacing(10)
        font_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._font_combo = QComboBox()
        self._font_combo.setMinimumWidth(280)
        self._font_combo.setMaxVisibleItems(12)
        from PyQt6.QtGui import QFontDatabase
        families = QFontDatabase.families()
        cjk_preferences = ["Microsoft YaHei", "Microsoft YaHei UI", "SimHei",
                           "Noto Sans SC", "SimSun", "KaiTi", "FangSong"]
        cjk = [f for f in families if not f.startswith("@")]
        preferred = [f for f in cjk if f in cjk_preferences]
        others = [f for f in cjk if f not in cjk_preferences]
        sorted_fonts = preferred + others
        self._font_combo.addItems(sorted_fonts)
        current = self._config.get("font_family")
        if current and current in cjk:
            self._font_combo.setCurrentText(current)
        self._font_combo.currentTextChanged.connect(
            lambda t: self._config.set("font_family", t)
        )
        font_layout.addRow("字体:", self._font_combo)

        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(12, 48)
        self._font_size_spin.setMinimumWidth(80)
        self._font_size_spin.setValue(self._config.get("font_size"))
        self._font_size_spin.valueChanged.connect(
            lambda v: self._config.set("font_size", v)
        )
        font_layout.addRow("字号:", self._font_size_spin)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Game settings
        game_group = QGroupBox("🎮 游戏设置")
        game_group.setStyleSheet(_GROUP_STYLE)
        game_layout = QFormLayout()
        game_layout.setSpacing(10)
        game_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._difficulty_slider = QSlider(Qt.Orientation.Horizontal)
        self._difficulty_slider.setRange(1, 6)
        self._difficulty_slider.setValue(self._config.get("difficulty"))
        self._difficulty_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._difficulty_slider.setTickInterval(1)
        self._diff_label = QLabel(str(self._config.get("difficulty")))
        self._diff_label.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT}; min-width: 20px;")
        diff_row = QHBoxLayout()
        diff_row.addWidget(self._difficulty_slider, stretch=1)
        diff_row.addWidget(self._diff_label)
        self._difficulty_slider.valueChanged.connect(self._on_difficulty_changed)
        game_layout.addRow("难度 (HSK):", diff_row)

        self._falling_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._falling_speed_slider.setRange(1, 5)
        self._falling_speed_slider.setValue(self._config.get("falling_speed"))
        self._falling_speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._falling_speed_slider.setTickInterval(1)
        self._speed_label = QLabel(str(self._config.get("falling_speed")))
        self._speed_label.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT}; min-width: 20px;")
        speed_row = QHBoxLayout()
        speed_row.addWidget(self._falling_speed_slider, stretch=1)
        speed_row.addWidget(self._speed_label)
        self._falling_speed_slider.valueChanged.connect(self._on_speed_changed)
        game_layout.addRow("掉落速度:", speed_row)

        self._timed_combo = QComboBox()
        self._timed_combo.setMinimumWidth(120)
        self._timed_combo.addItems(["60秒", "120秒", "180秒", "300秒"])
        durations = [60, 120, 180, 300]
        current_dur = self._config.get("timed_duration")
        if current_dur in durations:
            self._timed_combo.setCurrentIndex(durations.index(current_dur))
        self._timed_combo.currentIndexChanged.connect(
            lambda i: self._config.set("timed_duration", durations[i])
        )
        game_layout.addRow("限时挑战时长:", self._timed_combo)

        # Content ratio
        ratio_row = QHBoxLayout()
        self._ratio_slider = QSlider(Qt.Orientation.Horizontal)
        self._ratio_slider.setRange(10, 100)
        self._ratio_slider.setValue(self._config.get("content_ratio"))
        self._ratio_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._ratio_slider.setTickInterval(10)
        self._ratio_label = QLabel(f"{self._config.get('content_ratio')}%")
        self._ratio_label.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT}; min-width: 36px;")
        self._ratio_slider.valueChanged.connect(self._on_ratio_changed)
        ratio_row.addWidget(self._ratio_slider, stretch=1)
        ratio_row.addWidget(self._ratio_label)
        game_layout.addRow("内容量比例:", ratio_row)

        # Falling decoration pattern
        from src.ui.widgets.falling_item import DECO_LABELS
        self._deco_combo = QComboBox()
        self._deco_combo.setMinimumWidth(120)
        for key, label in DECO_LABELS.items():
            self._deco_combo.addItem(label, key)
        current_deco = self._config.get("falling_deco")
        idx = self._deco_combo.findData(current_deco)
        if idx >= 0:
            self._deco_combo.setCurrentIndex(idx)
        self._deco_combo.currentIndexChanged.connect(
            lambda i: self._config.set("falling_deco", self._deco_combo.itemData(i))
        )
        game_layout.addRow("掉落图案:", self._deco_combo)

        game_group.setLayout(game_layout)
        layout.addWidget(game_group)

        # Sound settings
        sound_group = QGroupBox("🔊 音效设置")
        sound_group.setStyleSheet(_GROUP_STYLE)
        sound_layout = QFormLayout()
        sound_layout.setSpacing(10)
        sound_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._sound_check = QCheckBox("启用音效")
        self._sound_check.setChecked(self._config.get("sound_enabled"))
        self._sound_check.stateChanged.connect(self._on_sound_toggled)
        sound_layout.addRow(self._sound_check)

        vol_row = QHBoxLayout()
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(int(self._config.get("sound_volume") * 100))
        self._volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._volume_slider.setTickInterval(10)
        self._volume_label = QLabel(f"{self._volume_slider.value()}%")
        self._volume_label.setStyleSheet(f"font-weight: bold; color: {COLOR_ACCENT}; min-width: 36px;")
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_row.addWidget(self._volume_slider, stretch=1)
        vol_row.addWidget(self._volume_label)
        sound_layout.addRow("音量:", vol_row)

        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)

        # Other settings
        other_group = QGroupBox("🌈 其他")
        other_group.setStyleSheet(_GROUP_STYLE)
        other_layout = QFormLayout()
        other_layout.setSpacing(10)

        self._auto_update_check = QCheckBox("自动更新素材 📥")
        self._auto_update_check.setChecked(self._config.get("auto_update_materials"))
        self._auto_update_check.stateChanged.connect(
            lambda s: self._config.set("auto_update_materials", bool(s))
        )
        other_layout.addRow(self._auto_update_check)

        self._rabbit_check = QCheckBox("显示键盘兔子")
        self._rabbit_check.setChecked(self._config.get("show_keyboard_rabbit"))
        self._rabbit_check.stateChanged.connect(
            lambda s: self._config.set("show_keyboard_rabbit", bool(s))
        )
        other_layout.addRow(self._rabbit_check)

        other_group.setLayout(other_layout)
        layout.addWidget(other_group)

        # Display settings
        display_group = QGroupBox("🖥️ 显示设置")
        display_group.setStyleSheet(_GROUP_STYLE)
        display_layout = QFormLayout()
        display_layout.setSpacing(10)
        display_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self._fullscreen_check = QCheckBox("全屏模式")
        self._fullscreen_check.setChecked(self._config.get("fullscreen_mode"))
        self._fullscreen_check.stateChanged.connect(self._on_fullscreen_toggled)
        display_layout.addRow(self._fullscreen_check)

        res_row = QHBoxLayout()
        self._res_combo = QComboBox()
        self._res_combo.setMinimumWidth(160)
        self._res_combo.addItems(["1024×768", "1280×800", "1280×1024", "1440×900", "1600×900", "1920×1080"])
        self._res_combo.setEnabled(not self._config.get("fullscreen_mode"))
        cur_w = self._config.get("window_width")
        cur_h = self._config.get("window_height")
        cur_res = f"{cur_w}×{cur_h}"
        idx = self._res_combo.findText(cur_res)
        if idx >= 0:
            self._res_combo.setCurrentIndex(idx)
        self._res_combo.currentTextChanged.connect(self._on_resolution_changed)
        res_row.addWidget(self._res_combo)
        display_layout.addRow("窗口分辨率:", res_row)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        layout.addStretch()
        scroll.setWidget(container)

    def _on_difficulty_changed(self, value):
        self._config.set("difficulty", value)
        self._diff_label.setText(str(value))

    def _on_speed_changed(self, value):
        self._config.set("falling_speed", value)
        self._speed_label.setText(str(value))

    def _on_ratio_changed(self, value):
        self._config.set("content_ratio", value)
        self._ratio_label.setText(f"{value}%")

    def _on_sound_toggled(self, state):
        enabled = bool(state)
        self._config.set("sound_enabled", enabled)
        App.instance().sound.set_enabled(enabled)

    def _on_volume_changed(self, value):
        vol = value / 100.0
        self._config.set("sound_volume", vol)
        App.instance().sound.set_volume(vol)
        self._volume_label.setText(f"{value}%")

    def _on_fullscreen_toggled(self, state):
        fullscreen = bool(state)
        self._config.set("fullscreen_mode", fullscreen)
        self._res_combo.setEnabled(not fullscreen)
        window = self.window()
        if hasattr(window, 'apply_display_mode'):
            w = self._config.get("window_width")
            h = self._config.get("window_height")
            window.apply_display_mode(fullscreen, w, h)

    def _on_resolution_changed(self, text: str):
        parts = text.split("×")
        if len(parts) == 2:
            w, h = int(parts[0]), int(parts[1])
            self._config.set("window_width", w)
            self._config.set("window_height", h)
            window = self.window()
            if hasattr(window, 'apply_display_mode'):
                window.apply_display_mode(False, w, h)
