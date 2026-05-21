import logging
import sqlite3
from datetime import datetime, timedelta
from src.utils.paths import get_app_dir
from src.constants import DB_FILENAME

SCHEMA_VERSION = 3

MIGRATIONS = {
    1: """
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT DEFAULT '',
            dynasty TEXT DEFAULT '',
            difficulty INTEGER DEFAULT 1,
            length INTEGER NOT NULL,
            tags TEXT DEFAULT '[]',
            content_hash TEXT UNIQUE NOT NULL,
            downloaded_at TEXT NOT NULL,
            is_local INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT NOT NULL,
            played_at TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            total_chars INTEGER NOT NULL,
            correct_chars INTEGER NOT NULL,
            accuracy REAL NOT NULL,
            cpm REAL DEFAULT 0,
            score INTEGER DEFAULT 0,
            max_combo INTEGER DEFAULT 0,
            difficulty INTEGER DEFAULT 1,
            material_source TEXT DEFAULT '',
            material_title TEXT DEFAULT ''
        );
    """,
    2: """
        CREATE INDEX IF NOT EXISTS idx_results_played_at ON game_results(played_at DESC);
        CREATE INDEX IF NOT EXISTS idx_results_mode ON game_results(mode);
        CREATE INDEX IF NOT EXISTS idx_materials_category ON materials(category);
        CREATE INDEX IF NOT EXISTS idx_materials_difficulty ON materials(difficulty);
    """,
    3: """
        ALTER TABLE materials ADD COLUMN is_favorite INTEGER DEFAULT 0;

        CREATE TABLE IF NOT EXISTS typing_mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER DEFAULT 0,
            played_at TEXT NOT NULL,
            mode TEXT NOT NULL,
            expected TEXT NOT NULL,
            actual TEXT DEFAULT '',
            position INTEGER DEFAULT 0,
            context TEXT DEFAULT '',
            material_source TEXT DEFAULT '',
            material_title TEXT DEFAULT '',
            FOREIGN KEY(result_id) REFERENCES game_results(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_mistakes_expected ON typing_mistakes(expected);
        CREATE INDEX IF NOT EXISTS idx_mistakes_played_at ON typing_mistakes(played_at DESC);
    """,
}


class DatabaseManager:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if DatabaseManager._instance is not None:
            raise RuntimeError("Use DatabaseManager.instance()")
        DatabaseManager._instance = self
        self._db_path = get_app_dir() / DB_FILENAME
        self._conn: sqlite3.Connection | None = None
        self._connect()
        self._run_migrations()

    def _connect(self):
        self._conn = sqlite3.connect(str(self._db_path), timeout=10)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def _run_migrations(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            )
        """)
        row = self._conn.execute("SELECT version FROM schema_version").fetchone()
        current = row[0] if row else 0

        for ver in sorted(MIGRATIONS.keys()):
            if ver > current:
                self._conn.executescript(MIGRATIONS[ver])
                if row:
                    self._conn.execute("UPDATE schema_version SET version = ?", (ver,))
                else:
                    self._conn.execute("INSERT INTO schema_version (version) VALUES (?)", (ver,))
                    row = True
                self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def create_thread_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection for use in a background thread."""
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def save_game_result(self, result: dict) -> int:
        """Save a game result. Returns the row id, or 0 on failure."""
        try:
            cursor = self._conn.execute("""
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
            self._conn.commit()
            return int(cursor.lastrowid or 0)
        except Exception as e:
            logging.warning("DatabaseManager: save_game_result failed: %s", e)
            return 0

    def save_typing_mistakes(self, result_id: int, mistakes: list[dict], meta: dict | None = None) -> int:
        """Persist per-character mistake events for review training."""
        if not mistakes:
            return 0
        meta = meta or {}
        played_at = meta.get("played_at") or datetime.now().isoformat()
        rows = []
        for event in mistakes:
            expected = event.get("expected", "")
            if not expected:
                continue
            rows.append((
                int(result_id or 0),
                played_at,
                meta.get("mode", ""),
                expected,
                event.get("actual", ""),
                int(event.get("position", 0)),
                event.get("context", ""),
                meta.get("material_source", ""),
                meta.get("material_title", ""),
            ))
        if not rows:
            return 0
        try:
            self._conn.executemany("""
                INSERT INTO typing_mistakes
                (result_id, played_at, mode, expected, actual, position, context, material_source, material_title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)
            self._conn.commit()
            return len(rows)
        except Exception as e:
            logging.warning("DatabaseManager: save_typing_mistakes failed: %s", e)
            return 0

    def query_stats(self, start: str, end: str) -> dict:
        """Query aggregate stats for a date range."""
        try:
            row = self._conn.execute("""
                SELECT COUNT(*),
                       ROUND(AVG(cpm), 1),
                       ROUND(AVG(accuracy), 4),
                       MAX(score),
                       MAX(max_combo),
                       COALESCE(SUM(score), 0)
                FROM game_results
                WHERE played_at >= ? AND played_at < ?
            """, (start, end)).fetchone()
            if row and row[0] > 0:
                return {
                    "count": row[0],
                    "avg_cpm": row[1] or 0,
                    "avg_accuracy": row[2] or 0,
                    "max_score": row[3] or 0,
                    "max_combo": row[4] or 0,
                    "total_score": row[5] or 0,
                }
        except Exception as e:
            logging.warning("DatabaseManager: query_stats failed: %s", e)
        return {"count": 0, "avg_cpm": 0, "avg_accuracy": 0, "max_score": 0, "max_combo": 0, "total_score": 0}

    def query_top_mistakes(self, limit: int = 8, start: str | None = None, end: str | None = None) -> list[dict]:
        """Return most frequent expected characters typed wrong."""
        try:
            params: list = []
            where = []
            if start and end:
                where.append("played_at >= ? AND played_at < ?")
                params.extend([start, end])
            query = """
                SELECT expected,
                       COUNT(*) AS mistake_count,
                       MAX(actual) AS last_actual,
                       MAX(context) AS sample_context,
                       MAX(material_title) AS material_title,
                       MAX(played_at) AS last_seen
                FROM typing_mistakes
            """
            if where:
                query += " WHERE " + " AND ".join(where)
            query += """
                GROUP BY expected
                ORDER BY mistake_count DESC, last_seen DESC
                LIMIT ?
            """
            params.append(limit)
            rows = self._conn.execute(query, params).fetchall()
            return [{
                "expected": r["expected"],
                "count": int(r["mistake_count"]),
                "last_actual": r["last_actual"] or "",
                "context": r["sample_context"] or "",
                "material_title": r["material_title"] or "",
                "last_seen": r["last_seen"] or "",
            } for r in rows]
        except Exception as e:
            logging.warning("DatabaseManager: query_top_mistakes failed: %s", e)
            return []

    def build_review_material(self, limit: int = 24) -> dict:
        """Build a short local review material from recent top mistakes."""
        mistakes = self.query_top_mistakes(limit=limit)
        chars = [m["expected"] for m in mistakes if m.get("expected")]
        if not chars:
            return {}
        text = "".join(chars)
        while len(text) < min(24, len(chars) * 4):
            text += "".join(chars)
        return {
            "title": "今日错字复训",
            "author": "",
            "category": "review",
            "content": text[:80],
            "difficulty": 1,
            "source": "local_mistakes",
        }

    def query_streak_days(self) -> int:
        """Return current consecutive practice days ending today."""
        try:
            rows = self._conn.execute("""
                SELECT DISTINCT DATE(played_at) AS day
                FROM game_results
                ORDER BY day DESC
                LIMIT 90
            """).fetchall()
            days = {str(r["day"]) for r in rows}
            today = datetime.now().date()
            streak = 0
            while (today - timedelta(days=streak)).isoformat() in days:
                streak += 1
            return streak
        except Exception as e:
            logging.warning("DatabaseManager: query_streak_days failed: %s", e)
            return 0

    def query_recent_material_titles(self, limit: int = 20) -> set[str]:
        try:
            rows = self._conn.execute("""
                SELECT DISTINCT material_title
                FROM game_results
                WHERE material_title != ''
                ORDER BY played_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return {str(r["material_title"]) for r in rows}
        except Exception as e:
            logging.warning("DatabaseManager: query_recent_material_titles failed: %s", e)
            return set()

    def query_daily_chart(self, start: str, end: str) -> list[tuple[str, int, float]]:
        """Query daily practice counts for chart."""
        try:
            rows = self._conn.execute("""
                SELECT DATE(played_at) as day, COUNT(*), ROUND(AVG(cpm), 1)
                FROM game_results
                WHERE played_at >= ? AND played_at < ?
                GROUP BY DATE(played_at)
                ORDER BY day ASC
                LIMIT 14
            """, (start, end)).fetchall()
            return [(str(r[0])[-5:], r[1], r[2]) for r in rows]
        except Exception as e:
            logging.warning("DatabaseManager: query_daily_chart failed: %s", e)
            return []

    def query_history(self, start: str | None = None, end: str | None = None, limit: int = 50) -> list[sqlite3.Row]:
        """Query game result history."""
        try:
            if start and end:
                return self._conn.execute("""
                    SELECT played_at, mode, cpm, accuracy, score, max_combo, material_title
                    FROM game_results
                    WHERE played_at >= ? AND played_at < ?
                    ORDER BY played_at DESC
                    LIMIT ?
                """, (start, end, limit)).fetchall()
            else:
                return self._conn.execute("""
                    SELECT played_at, mode, cpm, accuracy, score, max_combo, material_title
                    FROM game_results
                    ORDER BY played_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()
        except Exception as e:
            logging.warning("DatabaseManager: query_history failed: %s", e)
            return []

    def clear_game_results(self) -> bool:
        """Delete all game results. Returns True on success."""
        try:
            self._conn.execute("DELETE FROM game_results")
            self._conn.commit()
            return True
        except Exception as e:
            logging.warning("DatabaseManager: clear_game_results failed: %s", e)
            return False

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
