import logging
import aiosqlite
import os
from exception import send_message
from aiogram.types import Message
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()


class Execute:
    def __init__(self):
        self.connect_string = os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))
        self.conn = None

    @property
    async def auth_user(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_auth_user()
        except Exception as e:
            await send_message('Ошибка запроса в методе auth_user', os.getenv('EMAIL'), str(e))

    async def execute_auth_user(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_auth = f"SELECT ID_USER, STATUS FROM TELEGRAMMBOT "
            await cursor.execute(sql_auth)
            dict_user = {}
            row_table = await cursor.fetchall()
            for item in row_table:
                dict_user[int(item[0])] = item[1]
            return dict_user

    @property
    async def get_user_admin(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_user_admin()
        except Exception as e:
            await send_message('Ошибка запроса в методе get_user_admin', os.getenv('EMAIL'), str(e))

    async def execute_get_user_admin(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_user_admin = f"SELECT ID_USER FROM TELEGRAMMBOT " \
                             f"WHERE STATUS = 'creator' "
            await cursor.execute(sql_user_admin)
            user_admin = await cursor.fetchall()
            return user_admin

    async def start_message(self, message: Message):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_start_message(message)
        except Exception as e:
            await send_message('Ошибка запроса в методе start_message', os.getenv('EMAIL'), str(e))

    async def execute_start_message(self, message: Message):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_auth = f"SELECT ID_USER FROM TELEGRAMMBOT " \
                       f"WHERE ID_USER = {self.quote(message.from_user.id)} "
            await cursor.execute(sql_auth)
            row_table = await cursor.fetchone()
            if row_table is None:
                row_table = False
            else:
                row_table = True
            return row_table

    async def start_record_new_user(self, message: Message):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_start_record_new_user(message)
        except Exception as e:
            await send_message('Ошибка запроса в методе start_record_new_user', os.getenv('EMAIL'), str(e))

    async def execute_start_record_new_user(self, message: Message):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"INSERT INTO TELEGRAMMBOT (ID_USER, HISTORY, MESSAGES, CONTACT) " \
                         f"VALUES ({str(message.from_user.id)}, '/start', {str(message.message_id)}, " \
                         f"'empty///empty/////empty///empty///empty///empty///empty') "
            await cursor.execute(sql_record)
            print(f'Новый клиент {message.from_user.id} {message.from_user.first_name} {message.from_user.last_name} '
                  f'зашел с сообщением: {str(message.message_id)}')
            await self.conn.commit()

    async def restart_catalog(self, message: Message, element_history: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_restart_catalog(message, element_history)
        except Exception as e:
            await send_message('Ошибка запроса в методе restart_catalog', os.getenv('EMAIL'), str(e))

    async def execute_restart_catalog(self, message: Message, element_history: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"HISTORY = '{element_history}' " \
                         f"WHERE ID_USER = {self.quote(message.from_user.id)} "
            await cursor.execute(sql_record)
            if element_history == '/start':
                print(f'Клиент {message.from_user.id} {message.from_user.first_name} {message.from_user.last_name} '
                      f'возобновил работу с сообщением: {str(message.message_id)}')
            await self.conn.commit()

    async def get_element_history(self, id_user: int, index: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_element_history(id_user, index)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_element_history', os.getenv('EMAIL'), str(e))

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
