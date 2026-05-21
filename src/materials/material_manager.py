import json
import logging
import random
import threading
from src.utils.paths import get_data_dir


class MaterialManager:
    """Manages typing practice materials with thread-safe access."""

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._materials: list[dict] = []
        self._lock = threading.Lock()
        self._db_loaded = False

    def get_random(self, count: int = 1) -> list[dict]:
        with self._lock:
            self._ensure_loaded()
            if not self._materials:
                return []
            count = min(count, len(self._materials))
            return random.sample(self._materials, count)

    def get_random_material(self, category: str | None = None, difficulty: int | None = None) -> dict:
        with self._lock:
            self._ensure_loaded()
            pool = self._filter_unlocked(category=category, difficulty=difficulty)
            if not pool:
                pool = self._materials
            return random.choice(pool) if pool else self._fallback_materials()[0]

    def get_all(self) -> list[dict]:
        with self._lock:
            self._ensure_loaded()
            return list(self._materials)

    def get_materials(self, category: str | None = None) -> list[dict]:
        with self._lock:
            self._ensure_loaded()
            return list(self._filter_unlocked(category=category))

    def search(self, keyword: str) -> list[dict]:
        with self._lock:
            self._ensure_loaded()
            keyword = keyword.lower()
            return [m for m in self._materials if keyword in m.get("title", "").lower()
                    or keyword in m.get("content", "").lower()]

    def reload(self):
        with self._lock:
            self._materials.clear()
            self._db_loaded = False
            self._ensure_loaded()
            return len(self._materials)

    @property
    def count(self) -> int:
        with self._lock:
            self._ensure_loaded()
            return len(self._materials)

    def _ensure_loaded(self):
        """Load materials from DB if not already loaded. Must be called under self._lock."""
        if self._db_loaded:
            return
        self._db_loaded = True
        try:
            from src.db.database import DatabaseManager
            from src.materials.material_store import MaterialStore
            db = DatabaseManager.instance()
            store = MaterialStore(db.conn)
            db_materials = store.get_all(limit=200)
            self._materials.extend(db_materials)
        except Exception as e:
            logging.warning("MaterialManager: failed to load from DB: %s", e, exc_info=True)
        try:
            data_dir = get_data_dir()
            for json_file in data_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        self._materials.extend(self._normalize_material(item) for item in data)
                    elif isinstance(data, dict):
                        self._materials.append(self._normalize_material(data))
                except Exception as e:
                    logging.warning("MaterialManager: failed to load %s: %s", json_file, e)
        except Exception as e:
            logging.warning("MaterialManager: failed to scan data dir: %s", e)
        if not self._materials:
            self._materials.extend(self._fallback_materials())

    def _filter_unlocked(self, category: str | None = None, difficulty: int | None = None) -> list[dict]:
        pool = self._materials
        if category:
            cats = {"article"} if category == "article" else {category}
            if category == "article":
                cats.add("news")
            pool = [m for m in pool if m.get("category") in cats]
        if difficulty:
            pool = [m for m in pool if m.get("difficulty") == difficulty]
        return pool

    def _normalize_material(self, item: dict) -> dict:
        normalized = dict(item)
        if "title" not in normalized:
            normalized["title"] = normalized.get("word", "")
        if "content" not in normalized:
            normalized["content"] = normalized.get("word", "")
        if "category" not in normalized:
            normalized["category"] = "idiom" if normalized.get("word") else "article"
        if "difficulty" not in normalized:
            normalized["difficulty"] = 1
        return normalized

    def _fallback_materials(self) -> list[dict]:
        return [
            {
                "title": "静夜思",
                "author": "李白",
                "category": "poetry",
                "content": "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。",
                "difficulty": 1,
            },
            {
                "title": "春晓",
                "author": "孟浩然",
                "category": "poetry",
                "content": "春眠不觉晓，处处闻啼鸟。\n夜来风雨声，花落知多少。",
                "difficulty": 1,
            },
            {
                "title": "登鹳雀楼",
                "author": "王之涣",
                "category": "poetry",
                "content": "白日依山尽，黄河入海流。\n欲穷千里目，更上一层楼。",
                "difficulty": 2,
            },
        ]
