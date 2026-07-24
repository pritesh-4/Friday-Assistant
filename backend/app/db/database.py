"""Small asynchronous-friendly SQLite data layer for the single-user MVP."""

import asyncio
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

_log = get_logger("db.database")


class Database:
    """Run short SQLite operations outside FastAPI's event loop."""

    def __init__(self, database_url: str) -> None:
        self.configure(database_url)

    def configure(self, database_url: str) -> None:
        """Set the SQLite database used by the application or a test."""
        if not database_url.startswith("sqlite://"):
            raise ValueError("FRIDAY currently supports SQLite DATABASE_URL values only.")

        raw_path = database_url.removeprefix("sqlite://")
        if raw_path.startswith("//"):
            raw_path = "/" + raw_path.lstrip("/")
        elif raw_path.startswith("/."):
            # Fix for Windows where sqlite:///./friday.db becomes /./friday.db -> C:\friday.db
            raw_path = raw_path[1:]
        self.path = Path(raw_path).expanduser().resolve()

        # Ensure the parent directory exists immediately on configure so that
        # paths like /tmp/friday/friday.db are created before the first connect.
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Warn operators in production that SQLite data is ephemeral on
        # platforms like Render free tier (filesystem wiped on each redeploy).
        if settings.is_production:
            _log.warning(
                "[WARNING] Running SQLite in production mode. "
                "Database path: %s. "
                "Data will be LOST on redeploy if stored on an ephemeral filesystem (e.g., Render free tier). "
                "Consider migrating to a managed database for persistent storage.",
                self.path,
            )

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_sync(self) -> None:
        # Each migration is (version, list_of_sql_statements).
        # Using a list of statements instead of one big script allows us to
        # catch benign errors (e.g. "duplicate column") on a per-statement basis.
        migrations: list[tuple[int, list[str]]] = [

            (
                1,
                [
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        last_message TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        pinned INTEGER NOT NULL DEFAULT 0,
                        favorite INTEGER NOT NULL DEFAULT 0
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'completed',
                        citations TEXT,
                        context_awareness TEXT,
                        emotional_header TEXT
                    )
                    """,
                    """
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
                        ON messages(conversation_id, created_at)
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        value TEXT NOT NULL,
                        category TEXT NOT NULL DEFAULT 'general',
                        created_at TEXT NOT NULL
                    )
                    """,
                    "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)",
                    """
                    CREATE TABLE IF NOT EXISTS notes (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        priority TEXT NOT NULL DEFAULT 'medium',
                        due_date TEXT
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS user_settings (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        theme TEXT NOT NULL DEFAULT 'dark',
                        animations INTEGER NOT NULL DEFAULT 1,
                        voice_enabled INTEGER NOT NULL DEFAULT 1,
                        sidebar_collapsed INTEGER NOT NULL DEFAULT 0,
                        memory_enabled INTEGER NOT NULL DEFAULT 1,
                        notifications_enabled INTEGER NOT NULL DEFAULT 1
                    )
                    """,
                    """
                    CREATE TABLE IF NOT EXISTS files (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        storage_path TEXT NOT NULL UNIQUE,
                        created_at TEXT NOT NULL
                    )
                    """,
                ],
            ),
            (
                2,
                # SQLite ALTER TABLE does not support IF NOT EXISTS.
                # We apply each statement individually and ignore the
                # "duplicate column name" error so migrations are re-entrant.
                [
                    "ALTER TABLE memories ADD COLUMN source TEXT NOT NULL DEFAULT 'user'",
                    "ALTER TABLE memories ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0",
                    "ALTER TABLE memories ADD COLUMN updated_at TEXT",
                    "CREATE INDEX IF NOT EXISTS idx_memories_pinned ON memories(pinned)",
                ],
            ),
        ]

        with self._connect() as connection:
            current_version = connection.execute("PRAGMA user_version").fetchone()[0]
            for version, statements in migrations:
                if version > current_version:
                    for sql in statements:
                        try:
                            connection.execute(sql)
                        except Exception as exc:
                            # "duplicate column name" is harmless when a migration
                            # is applied to a DB that already has the column.
                            if "duplicate column name" in str(exc).lower():
                                continue
                            raise
                    connection.execute(f"PRAGMA user_version = {version}")  # nosec B608
            connection.execute("INSERT OR IGNORE INTO user_settings (id) VALUES (1)")

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    async def execute(self, query: str, parameters: Iterable[Any] = ()) -> int:
        def operation() -> int:
            with self._connect() as connection:
                cursor = connection.execute(query, tuple(parameters))
                return cursor.rowcount

        return await asyncio.to_thread(operation)

    async def fetch_one(
        self, query: str, parameters: Iterable[Any] = ()
    ) -> dict[str, Any] | None:
        def operation() -> dict[str, Any] | None:
            with self._connect() as connection:
                row = connection.execute(query, tuple(parameters)).fetchone()
                return dict(row) if row else None

        return await asyncio.to_thread(operation)

    async def fetch_all(
        self, query: str, parameters: Iterable[Any] = ()
    ) -> list[dict[str, Any]]:
        def operation() -> list[dict[str, Any]]:
            with self._connect() as connection:
                rows = connection.execute(query, tuple(parameters)).fetchall()
                return [dict(row) for row in rows]

        return await asyncio.to_thread(operation)


database = Database(settings.database_url)


async def get_db() -> Database:
    """FastAPI dependency exposing the application data store."""
    return database
