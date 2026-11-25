import aiosqlite
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

class Database:

    def __init__(self, path="data/poker.db"):
        self.path = path
        self.connection = None
    
    async def connect(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        
        if self.connection is None:
            self.connection = await aiosqlite.connect(self.path)
            self.connection.row_factory = aiosqlite.Row

        await self.connection.execute("PRAGMA foreign_keys = ON")
        return self.connection
    
    async def initialize(self):
        await self.connect()
        await self._apply_migrations()

    async def close(self):
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def _apply_migrations(self):
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)

        migration_dir = Path(__file__).parent / "migrations"
        migration_files = sorted(migration_dir.glob("*.sql"))

        cursor = await self.connection.execute(
            "SELECT version FROM schema_migrations"
        )

        rows = await cursor.fetchall()
        applied_migrations = {row["version"] for row in rows}

        for migration_file in migration_files:
            version = migration_file.name

            if version in applied_migrations:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            

            try:
                await self.connection.execute("BEGIN IMMEDIATE")
                statement = ""

                for line in sql.splitlines():
                    
                    statement += line + "\n"

                    if sqlite3.complete_statement(statement):
                        await self.connection.execute(statement)
                        statement = ""
                if statement.strip():
                    raise RuntimeError("migration ended with an incomplete SQL statement")

                await self.connection.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                    (version, datetime.now(timezone.utc).isoformat())
                )
                await self.connection.commit()
            
            except Exception:
                await self.connection.rollback()
                raise