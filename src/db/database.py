import sqlite3
from src.utils.paths import get_app_dir
from src.constants import DB_FILENAME

SCHEMA_VERSION = 2

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
}


class DatabaseManager:
    def __init__(self):
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

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
