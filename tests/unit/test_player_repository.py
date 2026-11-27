
import asyncio
import sqlite3

import pytest

from poker_bot.persistence.database import Database
from poker_bot.persistence.repositories.player_repository import PlayerRepository


async def setup_repository(tmp_path):
    db = Database(tmp_path / "test.db")
    await db.initialize()

    # Create a server because players have a foreign key to servers.
    await db.connection.execute(
        """
        INSERT INTO servers (guild_id, created_at)
        VALUES (?, ?)
        """,
        (12345, "2026-01-01T00:00:00+00:00"),
    )
    await db.connection.commit()

    repository = PlayerRepository(db)
    return db, repository


def test_create_player(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        await repo.create_player(12345, 67890, 1000)
        await db.connection.commit()

        player = await repo.get_player(12345, 67890)

        assert player is not None
        assert player["guild_id"] == 12345
        assert player["user_id"] == 67890
        assert player["balance"] == 1000
        assert player["registered_at"] is not None

        await db.close()

    asyncio.run(run_test())


def test_create_duplicate_player_raises_error(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        await repo.create_player(12345, 67890, 1000)
        await db.connection.commit()

        with pytest.raises(sqlite3.IntegrityError):
            await repo.create_player(12345, 67890, 1000)

        await db.close()

    asyncio.run(run_test())


def test_get_player_returns_none_when_missing(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        player = await repo.get_player(12345, 67890)

        assert player is None

        await db.close()

    asyncio.run(run_test())


def test_player_exists(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        await repo.create_player(12345, 67890, 1000)
        await db.connection.commit()

        assert await repo.player_exists(12345, 67890) is True
        assert await repo.player_exists(12345, 99999) is False

        await db.close()

    asyncio.run(run_test())


def test_get_balance(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        await repo.create_player(12345, 67890, 1000)
        await db.connection.commit()

        balance = await repo.get_balance(12345, 67890)

        assert balance == 1000

        await db.close()

    asyncio.run(run_test())


def test_get_balance_returns_zero(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        await repo.create_player(12345, 67890, 0)
        await db.connection.commit()

        balance = await repo.get_balance(12345, 67890)

        assert balance == 0

        await db.close()

    asyncio.run(run_test())


def test_get_balance_returns_none_when_player_missing(tmp_path):
    async def run_test():
        db, repo = await setup_repository(tmp_path)

        balance = await repo.get_balance(12345, 67890)

        assert balance is None

        await db.close()

    asyncio.run(run_test())
