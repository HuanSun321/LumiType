import json
import random
from src.utils.paths import get_data_dir


class MaterialManager:
    _instance = None

    def __init__(self):
        if MaterialManager._instance is not None:
            raise RuntimeError("Use MaterialManager.instance()")
        MaterialManager._instance = self
        self._materials: list[dict] = []
        self._db_loaded = False
        self._load_builtin()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_builtin(self):
        data_dir = get_data_dir()
        for json_file in data_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                if isinstance(items, list):
                    for item in items:
                        if "title" not in item:
                            item["title"] = item.get("word", "")
                        if "content" not in item:
                            item["content"] = item.get("word", "")
                        if "category" not in item:
                            item["category"] = "idiom"
                        self._materials.append(item)
            except Exception as e:
                print(f"Warning: failed to load {json_file}: {e}")

        if not self._materials:
            self._materials = self._fallback_materials()

    def _ensure_db_loaded(self):
        """Lazy-load DB materials on first access."""
        if self._db_loaded:
            return
        self._db_loaded = True
        try:
            from src.materials.material_store import MaterialStore
            store = MaterialStore()
            db_materials = store.get_all(limit=200)
            existing_hashes = {m.get("content") for m in self._materials}
            for m in db_materials:
                if m.get("content") not in existing_hashes:
                    self._materials.append({
                        "title": m.get("title", ""),
                        "author": m.get("author", ""),
                        "content": m.get("content", ""),
                        "category": m.get("category", "article"),
                        "difficulty": m.get("difficulty", 1),
                    })
        except Exception:
            pass

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

    def get_random_material(self, category: str | None = None, difficulty: int | None = None) -> dict:
        self._ensure_db_loaded()
        pool = self._materials
        if category:
            cats = {"article"} if category == "article" else {category}
            if category == "article":
                cats.add("news")
            pool = [m for m in pool if m.get("category") in cats]
        if difficulty:
            pool = [m for m in pool if m.get("difficulty") == difficulty]
        if not pool:
            pool = self._materials
        return random.choice(pool)

    def get_materials(self, category: str | None = None) -> list[dict]:
        self._ensure_db_loaded()
        if category:
            cats = {"article"} if category == "article" else {category}
            if category == "article":
                cats.add("news")
            return [m for m in self._materials if m.get("category") in cats]
        return list(self._materials)

    def reload(self):
        """Reload all materials from builtin files + database."""
        self._materials = []
        self._db_loaded = False
        self._load_builtin()
        self._ensure_db_loaded()
        return len(self._materials)

    @property
    def count(self) -> int:
        return len(self._materials)
