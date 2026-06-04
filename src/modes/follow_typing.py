"""Follow-typing mode: user types the displayed text sequentially."""
import logging

from src.core.game_state import GameMode
from src.materials.material_manager import MaterialManager
from src.modes.base_mode import BaseSequentialTypingMode

logger = logging.getLogger(__name__)


class FollowTypingMode(BaseSequentialTypingMode):
    mode = GameMode.FOLLOW_TYPING

    def __init__(self, category: str = None, ratio: float = 1.0, material: dict | None = None):
        super().__init__()
        if material:
            self._material = dict(material)
            text = self._material.get("content", "")
            logger.info(
                "FollowTypingMode.init custom_material title=%r category=%r content_len=%d ratio=%.3f",
                self._material.get("title", ""),
                self._material.get("category", ""),
                len(text),
                ratio,
            )
        else:
            mm = MaterialManager.instance()
            if category == "idiom":
                self._material, text = self.load_idiom_batch(mm)
            else:
                self._material = mm.get_random_material(category=category)
                text = self._material.get("content", "")
            logger.info(
                "FollowTypingMode.init random_material title=%r category=%r content_len=%d ratio=%.3f",
                self._material.get("title", ""),
                self._material.get("category", ""),
                len(text),
                ratio,
            )
        if ratio < 1.0 and text and (category or self._material.get("category")) in ("article", "news"):
            original_len = len(text)
            text = text[:max(1, int(len(text) * ratio))]
            logger.info(
                "FollowTypingMode.init truncated original_len=%d ratio=%.3f practice_len=%d",
                original_len,
                ratio,
                len(text),
            )
        if self._material.get("content", "") != text:
            self._material.setdefault("original_content", self._material.get("content", ""))
            self._material["content"] = text
        self.set_text(text.strip())
        logger.info(
            "FollowTypingMode.init final title=%r practice_len=%d material_content_len=%d",
            self._material.get("title", ""),
            len(self._text),
            len(self._material.get("content", "")),
        )

    def start(self):
        self.set_text(self._text)
        self._current_index = 0
        self._correct_count = 0
        self._total_typed = 0
        self._current_pinyin = ""

    @property
    def material(self) -> dict:
        return self._material

    def get_result(self) -> dict:
        return self._base_result("follow", self._material.get("title", ""))

    def is_game_over(self) -> bool:
        over = self._current_index >= len(self._text)
        if over:
            logger.info(
                "FollowTypingMode.is_game_over true cursor=%d text_len=%d title=%r",
                self._current_index,
                len(self._text),
                self._material.get("title", ""),
            )
        return over
