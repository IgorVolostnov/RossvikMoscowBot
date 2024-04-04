import logging
import aiosqlite
import os
from exception import send_message
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()


class Execute:
    def __init__(self):
        self.connect_string = os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))
        self.conn = None

    async def get_element_history(self, id_user: int, index: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_element_history(id_user, index)
        except Exception as e:
            await send_message('Ошибка запроса в функции current_history', os.getenv('EMAIL'), str(e))

    async def execute_get_element_history(self, id_user: int, index: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_history = f"SELECT HISTORY FROM TELEGRAMMBOT " \
                          f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_history)
            row_table = await cursor.fetchone()
            return row_table[0].split()[index]

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"
