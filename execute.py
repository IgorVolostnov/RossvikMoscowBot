import logging
import aiosqlite
import os
from exception import send_message
from aiogram.types import Message
from operator import itemgetter
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
            sql_auth = f"SELECT HISTORY, MESSAGES FROM TELEGRAMMBOT " \
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
            sql_record = f"INSERT INTO TELEGRAMMBOT (ID_USER, HISTORY, MESSAGES) " \
                         f"VALUES ({str(message.from_user.id)}, '/start', {str(message.message_id)}) "
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

    async def update_history(self, id_user: int, history: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_update_history(id_user, history)
        except Exception as e:
            await send_message('Ошибка запроса в методе add_element_history', os.getenv('EMAIL'), str(e))

    async def execute_update_history(self, id_user: int, history: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"HISTORY = '{history}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_element_history(self, id_user: int, amount_element: int):
        current = await self.get_info_user(id_user)
        if current[0] is None:
            current_history = ['/start']
        else:
            current_history = self.delete_element(current[0], amount_element)
            if len(current_history) == 0:
                current_history = ['/start']
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_delete_element_history(id_user, ' '.join(current_history))
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_element_history', os.getenv('EMAIL'), str(e))
        return current_history[-1]

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
            await send_message('Ошибка запроса в методе add_arr_messages', os.getenv('EMAIL'), str(e))

    async def execute_add_arr_messages(self, id_user: int, arr_messages: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"MESSAGES = '{arr_messages}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_message(self, user_id: int, record_message: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_record_message(user_id, record_message)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_message', os.getenv('EMAIL'), str(e))

    async def execute_record_message(self, user_id: int, record_message: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"MESSAGES = '{record_message}' " \
                         f"WHERE ID_USER = {self.quote(user_id)} "
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

    async def current_nomenclature(self, id_parent: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_nomenclature(id_parent)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_nomenclature', os.getenv('EMAIL'), str(e))

    async def execute_current_nomenclature(self, id_parent: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT KOD, NAME, SORT_NOMENCLATURE, PHOTO FROM NOMENCLATURE " \
                               f"WHERE CATEGORY_ID = '{id_parent}' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            return self.assembling_nomenclatures(row_table)

    async def current_description(self, kod_nomenclature: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_description(kod_nomenclature)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_description', os.getenv('EMAIL'), str(e))

    async def execute_current_description(self, kod_nomenclature: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT ARTICLE, BRAND, NAME, DISCOUNT, DESCRIPTION, SPECIFICATION, PHOTO, " \
                               f"AVAILABILITY, PRICE, DEALER, DISTRIBUTOR " \
                               f"FROM NOMENCLATURE " \
                               f"WHERE KOD = '{kod_nomenclature}' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchone()
            return row_table

    async def search_in_base_article(self, search_text: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_search_in_base_article(search_text)
        except Exception as e:
            await send_message('Ошибка запроса в методе search_in_base_article', os.getenv('EMAIL'), str(e))

    async def execute_search_in_base_article(self, search_text: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT KOD, NAME, SORT_NOMENCLATURE, PHOTO FROM NOMENCLATURE " \
                               f"WHERE ARTICLE_CHANGE LIKE '%{search_text}%' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            return set(row_table)

    async def search_in_base_name(self, search_text: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_search_in_base_name(search_text)
        except Exception as e:
            await send_message('Ошибка запроса в методе search_in_base_name', os.getenv('EMAIL'), str(e))

    async def execute_search_in_base_name(self, search_text: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT KOD, NAME, SORT_NOMENCLATURE, PHOTO FROM NOMENCLATURE " \
                               f"WHERE NAME LIKE '%{search_text}%' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            return set(row_table)

    async def current_basket(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_basket(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_basket', os.getenv('EMAIL'), str(e))

    async def execute_current_basket(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_basket = f"SELECT * FROM BASKET WHERE Id_user = {self.quote(id_user)} "
            await cursor.execute(sql_basket)
            basket = await cursor.fetchall()
            if len(basket) == 0:
                return None
            else:
                return self.assembling_basket(basket)

    async def current_amount_basket(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_amount_basket(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_amount_basket', os.getenv('EMAIL'), str(e))

    async def execute_current_amount_basket(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_basket = f"SELECT SUM(Amount) FROM BASKET WHERE Id_user = {self.quote(id_user)} "
            await cursor.execute(sql_basket)
            basket = await cursor.fetchone()
            if basket[0] is None:
                return None
            else:
                return basket[0]

    async def current_sum_basket(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_sum_basket(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_sum_basket', os.getenv('EMAIL'), str(e))

    async def execute_current_sum_basket(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_basket = f"SELECT SUM(Sum_price) FROM BASKET WHERE Id_user = {self.quote(id_user)} "
            await cursor.execute(sql_basket)
            basket = await cursor.fetchone()
            if basket[0] is None:
                return None
            else:
                return basket[0]

    async def current_nomenclature_basket(self, id_user: int, id_nomenclature: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_nomenclature_basket(id_user, id_nomenclature)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_nomenclature_basket', os.getenv('EMAIL'), str(e))

    async def execute_current_nomenclature_basket(self, id_user: int, id_nomenclature: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_basket = f"SELECT * FROM BASKET WHERE Id_user = {self.quote(id_user)} AND " \
                         f"Id_nomenclature = {self.quote(id_nomenclature)}"
            await cursor.execute(sql_basket)
            nomenclature = await cursor.fetchone()
            if nomenclature is None:
                return None
            else:
                return nomenclature

    async def add_basket_nomenclature(self, id_user: int, id_nomenclature: str, amount: float, sum_: float):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_add_basket_nomenclature(id_user, id_nomenclature, amount, sum_)
        except Exception as e:
            await send_message('Ошибка запроса в методе add_basket_nomenclature', os.getenv('EMAIL'), str(e))

    async def execute_add_basket_nomenclature(self, id_user: int, id_nomenclature: str, amount: float, sum_: float):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"INSERT INTO [BASKET] " \
                             f"([Id_user], [Id_nomenclature], [Amount], [Sum_price]) " \
                             f"VALUES ('{id_user}', " \
                             f"'{id_nomenclature}', " \
                             f"'{amount}', " \
                             f"'{sum_}') "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def update_basket_nomenclature(self, id_user: int, id_nomenclature: str, amount: float, sum_: float):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_update_basket_nomenclature(id_user, id_nomenclature, amount, sum_)
        except Exception as e:
            await send_message('Ошибка запроса в методе update_basket_nomenclature', os.getenv('EMAIL'), str(e))

    async def execute_update_basket_nomenclature(self, id_user: int, id_nomenclature: str, amount: float, sum_: float):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_update = f"UPDATE BASKET SET Amount = '{amount}'," \
                         f"Sum_price = '{sum_}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND " \
                         f"Id_nomenclature = {self.quote(id_nomenclature)}"
            await cursor.execute(sql_update)
            await self.conn.commit()

    async def delete_nomenclature_basket(self, id_user: int, id_nomenclature: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_delete_nomenclature_basket(id_user, id_nomenclature)
        except Exception as e:
            await send_message('Ошибка запроса в методе clean_basket', os.getenv('EMAIL'), str(e))

    async def execute_delete_nomenclature_basket(self, id_user: int, id_nomenclature: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_delete = f"DELETE FROM BASKET WHERE Id_user = {self.quote(id_user)} AND " \
                         f"Id_nomenclature = {self.quote(id_nomenclature)}"
            await cursor.execute(sql_delete)
            await self.conn.commit()

    async def clean_basket(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_clean_basket(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе clean_basket', os.getenv('EMAIL'), str(e))

    async def execute_clean_basket(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_delete = f"DELETE FROM BASKET WHERE Id_user = {self.quote(id_user)}"
            await cursor.execute(sql_delete)
            await self.conn.commit()

    async def get_arr_order(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_arr_order(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_arr_order', os.getenv('EMAIL'), str(e))

    async def execute_get_arr_order(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_order = f"SELECT ORDER_USER FROM TELEGRAMMBOT " \
                            f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_arr_order)
            row_table = await cursor.fetchone()
            return self.get_arr_orders(row_table[0])

    async def record_order(self, id_user: int, list_order: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order(id_user, list_order)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order', os.getenv('EMAIL'), str(e))

    async def execute_record_order(self, id_user: int, list_order: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"ORDER_USER = '{list_order}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def get_arr_contact(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_arr_contact(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_arr_contact', os.getenv('EMAIL'), str(e))

    async def execute_get_arr_contact(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_contact = f"SELECT CONTACT FROM TELEGRAMMBOT " \
                              f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_arr_contact)
            row_table = await cursor.fetchone()
            return row_table[0]

    async def record_contact(self, id_user: int, delivery: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_contact(id_user, delivery)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_contact', os.getenv('EMAIL'), str(e))

    async def execute_record_contact(self, id_user: int, delivery: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"CONTACT = '{delivery}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def get_delivery_address(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_delivery_address(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_delivery_address', os.getenv('EMAIL'), str(e))

    async def execute_get_delivery_address(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_order = f"SELECT DELIVERY_ADDRESS FROM TELEGRAMMBOT " \
                            f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_arr_order)
            row_table = await cursor.fetchone()
            return row_table[0]

    async def record_delivery(self, id_user: int, current_delivery: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_delivery(id_user, current_delivery)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_delivery', os.getenv('EMAIL'), str(e))

    async def execute_record_delivery(self, id_user: int, current_delivery: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"DELIVERY_ADDRESS = '{current_delivery}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def clean_delivery(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_clean_delivery(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе clean_delivery', os.getenv('EMAIL'), str(e))

    async def execute_clean_delivery(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"DELIVERY_ADDRESS = NULL " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def get_content_delivery(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_content_delivery(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_delivery_address', os.getenv('EMAIL'), str(e))

    async def execute_get_content_delivery(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_content = f"SELECT CONTENT_DELIVERY FROM TELEGRAMMBOT " \
                            f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_arr_content)
            row_table = await cursor.fetchone()
            return row_table[0]

    async def record_content_delivery(self, id_user: int, content_delivery: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_content_delivery(id_user, content_delivery)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_delivery', os.getenv('EMAIL'), str(e))

    async def execute_record_content_delivery(self, id_user: int, current_delivery: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"CONTENT_DELIVERY = '{current_delivery}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def clean_content_delivery(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_clean_content_delivery(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе clean_delivery', os.getenv('EMAIL'), str(e))

    async def execute_clean_content_delivery(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"CONTENT_DELIVERY = f'empty_____None/////empty_____None/////empty_____None/////" \
                         f"empty_____None/////empty_____None/////empty_____None/////empty_____None/////" \
                         f"empty_____None/////empty_____None' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

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

    @staticmethod
    def assembling_nomenclatures(arr: list):
        assembling_dict_nomenclatures = {}
        dict_m = {}
        i = 1
        y = 1
        for item_nomenclature in sorted(arr, key=itemgetter(2), reverse=False):
            if i < 7:
                dict_m[item_nomenclature[0]] = [item_nomenclature[1], item_nomenclature[3]]
                i += 1

            else:
                assembling_dict_nomenclatures['Стр.' + str(y)] = dict_m
                i = 1
                dict_m = {}
                y += 1
                dict_m[item_nomenclature[0]] = [item_nomenclature[1], item_nomenclature[3]]
                i += 1
        assembling_dict_nomenclatures['Стр.' + str(y)] = dict_m
        return assembling_dict_nomenclatures

    @staticmethod
    def assembling_basket(arr: list):
        assembling_dict_basket = {}
        dict_m = {}
        i = 1
        y = 1
        for item_nomenclature in arr:
            if i < 4:
                dict_m[item_nomenclature[1]] = [item_nomenclature[2], item_nomenclature[3]]
                i += 1
            else:
                assembling_dict_basket['Корзина_Стр.' + str(y)] = dict_m
                i = 1
                dict_m = {}
                y += 1
                dict_m[item_nomenclature[1]] = [item_nomenclature[2], item_nomenclature[3]]
                i += 1
        assembling_dict_basket['Корзина_Стр.' + str(y)] = dict_m
        return assembling_dict_basket

    @staticmethod
    def get_basket_dict(basket: str):
        basket_dict = {}
        if basket is None:
            basket_dict = {}
        else:
            for item in basket.split():
                row = item.split('///')
                basket_dict[row[0]] = [row[1], row[2]]
        return basket_dict

    @staticmethod
    def get_arr_orders(orders: str):
        if orders is None:
            arr_orders = []
        else:
            arr_orders = orders
        return arr_orders
