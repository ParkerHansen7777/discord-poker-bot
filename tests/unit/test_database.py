
import asyncio
import sqlite3

import pytest

import poker_bot.persistence.database as database_module
from poker_bot.persistence.database import Database


def test_connect_creates_database(tmp_path):
    async def run_test():
        db_path = tmp_path / "nested" / "test.db"
        db = Database(db_path)

        connection = await db.connect()

        assert connection is not None
        assert db_path.exists()
        assert db.connection is connection

        cursor = await connection.execute("PRAGMA foreign_keys")
        result = await cursor.fetchone()
        assert result[0] == 1

        await db.close()

    asyncio.run(run_test())


def test_initialize_creates_tables(tmp_path):
    async def run_test():
        db = Database(tmp_path / "test.db")

        await db.initialize()

        cursor = await db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
        rows = await cursor.fetchall()
        table_names = {row["name"] for row in rows}

        expected_tables = {
            "schema_migrations",
            "servers",
            "players",
            "loans",
            "transactions",
        }

        assert expected_tables.issubset(table_names)

        await db.close()

    asyncio.run(run_test())


def test_initialize_records_migration(tmp_path):
    async def run_test():
        db = Database(tmp_path / "test.db")

        await db.initialize()

        cursor = await db.connection.execute(
            "SELECT version FROM schema_migrations"
        )
        rows = await cursor.fetchall()

        versions = {row["version"] for row in rows}

        assert "001_initial_schema.sql" in versions

        await db.close()

    asyncio.run(run_test())


def test_initialize_twice_does_not_duplicate_migrations(tmp_path):
    async def run_test():
        db = Database(tmp_path / "test.db")

        await db.initialize()
        await db.initialize()

        cursor = await db.connection.execute(
            "SELECT COUNT(*) FROM schema_migrations"
        )
        result = await cursor.fetchone()

        assert result[0] == 1

        await db.close()

    asyncio.run(run_test())


def test_failed_migration_rolls_back_changes(tmp_path, monkeypatch):
    async def run_test():
        # Create an isolated migration directory.
        migration_dir = tmp_path / "migrations"
        migration_dir.mkdir()

        migration_file = migration_dir / "001_invalid_migration.sql"
        migration_file.write_text(
            """
            CREATE TABLE rollback_test (
                id INTEGER PRIMARY KEY
            );

            INVALID SQL STATEMENT;
            """,
            encoding="utf-8",
        )

        # Redirect the Database class to our temporary migration directory.
        fake_module_path = tmp_path / "database.py"
        monkeypatch.setattr(
            database_module,
            "__file__",
            str(fake_module_path),
        )

        db = Database(tmp_path / "test.db")

        with pytest.raises(sqlite3.OperationalError):
            await db.initialize()

        # The table created before the invalid statement should be rolled back.
        cursor = await db.connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'rollback_test'
            """
        )
        result = await cursor.fetchone()

        assert result is None

        # The failed migration must not be recorded.
        cursor = await db.connection.execute(
            "SELECT version FROM schema_migrations"
        )
        rows = await cursor.fetchall()

        assert rows == []

        await db.close()

    asyncio.run(run_test())


def test_foreign_keys_reject_invalid_player(tmp_path):
    async def run_test():
        db = Database(tmp_path / "test.db")

        await db.initialize()

        with pytest.raises(sqlite3.IntegrityError):
            await db.connection.execute(
                """
                INSERT INTO players (guild_id, user_id, registered_at)
                VALUES (?, ?, ?)
                """,
                (12345, 67890, "2026-01-01T00:00:00+00:00"),
            )

        await db.close()

    asyncio.run(run_test())


def test_close_and_reconnect(tmp_path):
    async def run_test():
        db = Database(tmp_path / "test.db")

        first_connection = await db.connect()

        await db.close()

        assert db.connection is None

        second_connection = await db.connect()

        assert second_connection is not None
        assert db.connection is second_connection

        await db.close()

    asyncio.run(run_test())
