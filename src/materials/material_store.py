import hashlib
import json
from datetime import datetime
from src.app import App


class MaterialStore:
    """Store and retrieve materials from SQLite."""

    def __init__(self, conn=None):
        self._db = conn or App.instance().db.conn

    def save(self, material: dict) -> bool:
        """Save a material item. Returns True if new, False if duplicate."""
        content = material.get("content", "")
        content_hash = material.get("content_hash") or hashlib.sha256(content.encode("utf-8")).hexdigest()

        try:
            cursor = self._db.execute("""
                INSERT OR IGNORE INTO materials
                (source, category, title, content, author, dynasty, difficulty, length, tags, content_hash, downloaded_at, is_local)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                material.get("source", ""),
                material.get("category", ""),
                material.get("title", ""),
                content,
                material.get("author", ""),
                material.get("dynasty", ""),
                material.get("difficulty", 1),
                len(content),
                json.dumps(material.get("tags", []), ensure_ascii=False),
                content_hash,
                datetime.now().isoformat(),
            ))
            self._db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

    def save_batch(self, materials: list[dict]) -> int:
        """Save multiple materials in a single transaction. Returns count of new items."""
        saved = 0
        for m in materials:
            content = m.get("content", "")
            content_hash = m.get("content_hash") or hashlib.sha256(content.encode("utf-8")).hexdigest()
            try:
                cursor = self._db.execute("""
                    INSERT OR IGNORE INTO materials
                    (source, category, title, content, author, dynasty, difficulty, length, tags, content_hash, downloaded_at, is_local)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (
                    m.get("source", ""),
                    m.get("category", ""),
                    m.get("title", ""),
                    content,
                    m.get("author", ""),
                    m.get("dynasty", ""),
                    m.get("difficulty", 1),
                    len(content),
                    json.dumps(m.get("tags", []), ensure_ascii=False),
                    content_hash,
                    datetime.now().isoformat(),
                ))
                if cursor.rowcount > 0:
                    saved += 1
            except Exception:
                continue
        self._db.commit()
        return saved

    def get_all(self, category: str | None = None, difficulty: int | None = None,
                limit: int = 100) -> list[dict]:
        query = "SELECT * FROM materials"
        conditions = []
        params: list = []
        if category:
            conditions.append("category = ?")
            params.append(category)
        if difficulty:
            conditions.append("difficulty = ?")
            params.append(difficulty)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY downloaded_at DESC LIMIT ?"
        params.append(limit)

        rows = self._db.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def search(self, keyword: str, limit: int = 20) -> list[dict]:
        query = """
            SELECT * FROM materials
            WHERE title LIKE ? OR content LIKE ? OR author LIKE ?
            ORDER BY difficulty, length
            LIMIT ?
        """
        pattern = f"%{keyword}%"
        rows = self._db.execute(query, (pattern, pattern, pattern, limit)).fetchall()
        return [dict(r) for r in rows]

    def count(self, category: str | None = None) -> int:
        if category:
            row = self._db.execute(
                "SELECT COUNT(*) FROM materials WHERE category = ?", (category,)
            ).fetchone()
        else:
            row = self._db.execute("SELECT COUNT(*) FROM materials").fetchone()
        return row[0] if row else 0