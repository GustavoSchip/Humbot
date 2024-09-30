from typing import Optional

from aiosqlite import Connection


class DatabaseManager:
    def __init__(self, *, connection: Connection) -> None:
        self.connection = connection

    async def set_bbb_id(self, user_id: int, bbb_id: str, bbb_name: str) -> bool:
        """
        This function will link a BBB ID and an ID of the user to the database.

        :param user_id: The ID of the user that should be linked.
        :param bbb_id: The BBB ID of the user that should be linked.
        :param bbb_name: The BBB name the user that should be linked.
        """
        await self.connection.execute("INSERT INTO bbb(user_id, bbb_id, bbb_name) VALUES (?, ?, ?)",
                                      (user_id, bbb_id, bbb_name))
        await self.connection.commit()
        async with self.connection.execute("SELECT COUNT(*) FROM bbb WHERE user_id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] > 0 if result is not None else False

    async def remove_bbb_id(self, user_id: int) -> bool:
        """
        This function will remove a link from the database.

        :param user_id: The ID of the user that should be unlinked.
        """
        await self.connection.execute("DELETE FROM bbb WHERE user_id=?", (user_id,))
        await self.connection.commit()
        async with self.connection.execute("SELECT COUNT(*) FROM bbb WHERE user_id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] == 0 if result is not None else False

    async def get_bbb_id(self, user_id: int) -> Optional[tuple[str]]:
        """
        This function will retrieve the BBB ID for a given user ID.

        :param user_id: The ID of the user whose BBB ID should be retrieved.
        :return: The BBB ID of the user.
        """
        async with self.connection.execute("SELECT bbb_id, bbb_name FROM bbb WHERE user_id=?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return (result[0], result[1]) if result is not None else None
