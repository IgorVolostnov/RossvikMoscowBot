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

    async def get_info_user(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_info_user(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_info_user', os.getenv('EMAIL'), str(e))

    async def execute_get_info_user(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_auth = f"SELECT HISTORY, MESSAGES, ORDER_USER FROM TELEGRAMMBOT " \
                       f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_auth)
            row_table = await cursor.fetchone()
            return row_table

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

    async def get_arr_history(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_arr_history(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_arr_history', os.getenv('EMAIL'), str(e))

    async def execute_get_arr_history(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_order = f"SELECT HISTORY FROM TELEGRAMMBOT " \
                            f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_arr_order)
            row_table = await cursor.fetchone()
            if row_table[0] is None:
                arr_history = []
            else:
                arr_history = row_table[0].split()
            return arr_history

    async def add_element_history(self, id_user: int, history: str):
        current = await self.get_info_user(id_user)
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_add_history(id_user, self.add_element(current[0], history))
        except Exception as e:
            await send_message('Ошибка запроса в методе add_element_history', os.getenv('EMAIL'), str(e))

    async def execute_add_history(self, id_user: int, history: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"HISTORY = '{history}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_element_history(self, id_user: int, amount_element: int):
        current = await self.get_info_user(id_user)
        current_history = self.delete_element(current[0], amount_element)
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_delete_element_history(id_user, ' '.join(current_history))
                return current_history[-1]
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_element_history', os.getenv('EMAIL'), str(e))

    async def execute_delete_element_history(self, id_user: int, history: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"HISTORY = '{history}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def get_arr_messages(self, user_id: int, except_id_message: int = None):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_arr_messages(user_id, except_id_message)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_arr_messages', os.getenv('EMAIL'), str(e))

    async def execute_get_arr_messages(self, user_id: int, except_id_message: int = None):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_number_chat = f"SELECT MESSAGES FROM TELEGRAMMBOT " \
                              f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_number_chat)
            row_table = await cursor.fetchone()
            arr_messages = row_table[0].split()
            if except_id_message:
                arr_messages.remove(str(except_id_message))
            return arr_messages

    async def add_element_message(self, id_user: int, message_id: int):
        current = await self.get_info_user(id_user)
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_add_message(id_user, self.add_element(current[1], str(message_id)))
        except Exception as e:
            await send_message('Ошибка запроса в методе add_element_message', os.getenv('EMAIL'), str(e))

    async def execute_add_message(self, id_user: int, arr_messages: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"MESSAGES = '{arr_messages}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def add_arr_messages(self, id_user: int, arr_message_id: list):
        current = await self.get_info_user(id_user)
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_add_arr_messages(id_user, self.add_arr_element(current[1], arr_message_id))
        except Exception as e:
            await send_message('Ошибка запроса в методе add_element_message', os.getenv('EMAIL'), str(e))

    async def execute_add_arr_messages(self, id_user: int, arr_messages: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"MESSAGES = '{arr_messages}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def current_category(self, id_parent: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_category(id_parent)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_category', os.getenv('EMAIL'), str(e))

    async def execute_current_category(self, id_parent: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT KOD, NAME_CATEGORY, SORT_CATEGORY FROM CATEGORY " \
                           f"WHERE PARENT_ID = '{id_parent}' "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            return row_table

    async def text_category(self, id_category: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_text_category(id_category)
        except Exception as e:
            await send_message('Ошибка запроса в методе text_category', os.getenv('EMAIL'), str(e))

    async def execute_text_category(self, id_category: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT NAME_CATEGORY FROM CATEGORY " \
                           f"WHERE KOD = '{id_category}' "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchone()
            return row_table[0]

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"

    @staticmethod
    def add_element(arr: str, element: str):
        arr_element = arr.split()
        arr_element.append(element)
        return ' '.join(arr_element)

    @staticmethod
    def add_arr_element(arr_string: str, arr_element: list):
        arr = arr_string.split()
        for item in arr_element:
            arr.append(item)
        return ' '.join(arr)

    @staticmethod
    def delete_element(arr: str, amount: int):
        arr_element = arr.split()
        for item in range(amount):
            arr_element.pop()
        return arr_element
