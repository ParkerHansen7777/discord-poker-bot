from poker_bot.persistence.database import Database
from datetime import datetime, timezone


class PlayerRepository:

    def __init__(self, database: Database):
        self.database = database

    async def create_player(self, guild_id: int, user_id: int, balance: int):

        timestamp = datetime.now(timezone.utc).isoformat()

        await self.database.connection.execute(
            "INSERT INTO players (guild_id, user_id, balance, registered_at) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, balance, timestamp)
        )

    async def get_player(self, guild_id: int, user_id: int):

        cursor = await self.database.connection.execute(
            "SELECT * FROM players WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )

        player = await cursor.fetchone()
        return player

    async def player_exists(self, guild_id: int, user_id: int) -> bool:

        cursor = await self.database.connection.execute(
            "SELECT EXISTS (SELECT 1 from players WHERE guild_id = ? AND user_id = ?)",
            (guild_id, user_id)
        )

        player = await cursor.fetchone()
        return bool(player[0])

    async def get_balance(self, guild_id: int, user_id: int) -> int | None:

        cursor = await self.database.connection.execute(
            "SELECT balance FROM players WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )

        balance = await cursor.fetchone()

        return balance["balance"] if balance is not None else None