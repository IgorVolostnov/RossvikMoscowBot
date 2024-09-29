import json
import logging
import aiosqlite
import os
import datetime
from prettytable import PrettyTable
from exception import send_message
from aiogram.types import Message
from operator import itemgetter

logging.basicConfig(level=logging.INFO)


class Execute:
    def __init__(self):
        self.connect_string = os.path.join(os.path.split(os.path.dirname(__file__))[0], os.environ["CONNECTION"])
        self.conn = None

    @property
    async def auth_user(self) -> dict:
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_auth_user()
        except Exception as e:
            await send_message('Ошибка запроса в методе auth_user', os.environ["EMAIL"], str(e))

    async def execute_auth_user(self) -> dict:
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_auth = f"SELECT ID_USER, STATUS, LANGUAGE, DISCOUNT FROM TELEGRAMMBOT "
            await cursor.execute(sql_auth)
            dict_user = {}
            row_table = await cursor.fetchall()
            for item in row_table:
                status_user = json.loads(item[1])
                dict_user[int(item[0])] = {'status': status_user, 'lang': item[2], 'discount_user': item[3]}
            return dict_user

    async def status_user(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_status_user(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе status_user', os.environ["EMAIL"], str(e))

    async def execute_status_user(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_auth = f"SELECT STATUS FROM TELEGRAMMBOT " \
                       f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_auth)
            row_table = await cursor.fetchone()
            if row_table is None:
                print('No user')
            else:
                status_user = json.loads(row_table[0])
            return status_user["status"]

    @property
    async def get_user_admin(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_user_admin()
        except Exception as e:
            await send_message('Ошибка запроса в методе get_user_admin', os.environ["EMAIL"], str(e))

    async def execute_get_user_admin(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_user_admin = f"SELECT ID_USER FROM TELEGRAMMBOT " \
                             f"WHERE STATUS = 'creator' "
            await cursor.execute(sql_user_admin)
            user_admin = await cursor.fetchall()
            return user_admin

    @property
    async def get_list_user_without_creator(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_list_user_without_creator()
        except Exception as e:
            await send_message('Ошибка запроса в методе get_list_user_without_creator', os.environ["EMAIL"], str(e))

    async def execute_get_list_user_without_creator(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_list_user = f"SELECT ID_USER FROM TELEGRAMMBOT " \
                             f"WHERE STATUS = 'dealer' OR STATUS = 'distributor' OR STATUS = 'admin' OR STATUS IS NULL"
            await cursor.execute(sql_list_user)
            user_admin = await cursor.fetchall()
            return user_admin

    async def list_user_for_add_status(self, username: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_list_user_for_add_status(username)
        except Exception as e:
            await send_message('Ошибка запроса в методе list_user_for_add_status', os.environ["EMAIL"], str(e))

    async def execute_list_user_for_add_status(self, username: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_list_user = f"SELECT ID_USER, USER_NAME_USER FROM TELEGRAMMBOT " \
                            f"WHERE USER_NAME_USER LIKE '%{username}%' "
            await cursor.execute(sql_list_user)
            list_user = await cursor.fetchall()
            if list_user is None:
                dict_user = False
            else:
                dict_user = {}
                for item in list_user:
                    dict_user[f'identifier{item[0]}'] = item[1]
            return dict_user

    async def set_retail_customer(self, user_id: str, status_user: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_set_retail_customer(user_id, status_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе set_retail_customer', os.environ["EMAIL"], str(e))

    async def execute_set_retail_customer(self, user_id: str, status_user: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"STATUS = '{status_user}' " \
                         f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def set_dealer(self, user_id: str, status_user: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_set_dealer(user_id, status_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе set_dealer', os.environ["EMAIL"], str(e))

    async def execute_set_dealer(self, user_id: str, status_user: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"STATUS = '{status_user}' " \
                         f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def set_distributor(self, user_id: str, status_user: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_set_distributor(user_id, status_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе set_distributor', os.environ["EMAIL"], str(e))

    async def execute_set_distributor(self, user_id: str, status_user: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"STATUS = '{status_user}' " \
                         f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def set_discount_amount(self, user_id: str, status_user: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_set_discount_amount(user_id, status_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе set_discount_amount', os.environ["EMAIL"], str(e))

    async def execute_set_discount_amount(self, user_id: str, status_user: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"STATUS = '{status_user}' " \
                         f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_user(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_delete_user(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_user', os.environ["EMAIL"], str(e))

    async def execute_delete_user(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_delete = f"DELETE FROM TELEGRAMMBOT WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_delete)
            await self.conn.commit()

    async def get_info_user(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_info_user(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_info_user', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе start_message', os.environ["EMAIL"], str(e))

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

    async def start_record_new_user(self, message: Message) -> list:
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_start_record_new_user(message)
        except Exception as e:
            await send_message('Ошибка запроса в методе start_record_new_user', os.environ["EMAIL"], str(e))

    async def execute_start_record_new_user(self, message: Message) -> list:
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            status_user = {'status': 'buyer', 'consumables': 0, 'tool': 0, 'compressor': 0, 'extra_discount': 0}
            status_user_str = json.dumps(status_user)
            sql_record = f"INSERT INTO TELEGRAMMBOT (ID_USER, HISTORY, MESSAGES, STATUS, FIRST_NAME_USER, " \
                         f"LAST_NAME_USER, USER_NAME_USER, DISCOUNT, LANGUAGE) " \
                         f"VALUES (" \
                         f"'{str(message.from_user.id)}', " \
                         f"'/start', " \
                         f"'{str(message.message_id)}', " \
                         f"'{status_user_str}', " \
                         f"'{message.from_user.first_name}', " \
                         f"'{message.from_user.last_name}', " \
                         f"'{message.from_user.username}', " \
                         f"'{0}'," \
                         f"'russian') "
            await cursor.execute(sql_record)
            print(f'Новый клиент ID: {message.from_user.id} {message.from_user.first_name} '
                  f'{message.from_user.last_name} c username: {message.from_user.username} '
                  f'зашел с сообщением: {str(message.message_id)}')
            await self.conn.commit()
            return [message.from_user.id, status_user, 'russian']

    async def restart_catalog(self, message: Message, element_history: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_restart_catalog(message, element_history)
        except Exception as e:
            await send_message('Ошибка запроса в методе restart_catalog', os.environ["EMAIL"], str(e))

    async def execute_restart_catalog(self, message: Message, element_history: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"HISTORY = '{element_history}'," \
                         f"FIRST_NAME_USER =  '{message.from_user.first_name}'," \
                         f"LAST_NAME_USER =  '{message.from_user.last_name}'," \
                         f"USER_NAME_USER =  '{message.from_user.username}' " \
                         f"WHERE ID_USER = {self.quote(message.from_user.id)} "
            await cursor.execute(sql_record)
            if element_history == '/start':
                print(f'Клиент ID: {message.from_user.id} {message.from_user.first_name} {message.from_user.last_name} '
                      f'c username: {message.from_user.username} '
                      f'возобновил работу с сообщением: {str(message.message_id)}')
            await self.conn.commit()

    async def get_element_history(self, id_user: int, index: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_element_history(id_user, index)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_element_history', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе get_arr_history', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе add_element_history', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе update_history', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе delete_element_history', os.environ["EMAIL"], str(e))
        return current_history[-1]

    async def execute_delete_element_history(self, id_user: int, history: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"HISTORY = '{history}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_element_history_before_value(self, id_user: int, value: str):
        current = await self.get_info_user(id_user)
        if current[0] is None:
            current_history = ['/start']
        else:
            current_history = self.delete_element_before_value(current[0], value)
            if len(current_history) == 0:
                current_history = ['/start']
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_delete_element_history_before_value(id_user, ' '.join(current_history))
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_element_history', os.environ["EMAIL"], str(e))
        return current_history[-1]

    async def execute_delete_element_history_before_value(self, id_user: int, history: str):
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
            await send_message('Ошибка запроса в методе get_arr_messages', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе add_element_message', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе add_arr_messages', os.environ["EMAIL"], str(e))

    async def execute_add_arr_messages(self, id_user: int, arr_messages: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"MESSAGES = '{arr_messages}' " \
                         f"WHERE ID_USER = {self.quote(id_user)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def add_list_element_message(self, dict_user: dict):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_add_list_element_message(dict_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе add_list_element_message', os.environ["EMAIL"], str(e))

    async def execute_add_list_element_message(self, dict_user: dict):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            for key, item in dict_user.items():
                sql_record = f"UPDATE TELEGRAMMBOT SET " \
                             f"MESSAGES = '{item}' " \
                             f"WHERE ID_USER = {self.quote(key)} "
                await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_message(self, user_id: int, record_message: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_record_message(user_id, record_message)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_message', os.environ["EMAIL"], str(e))

    async def execute_record_message(self, user_id: int, record_message: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE TELEGRAMMBOT SET " \
                         f"MESSAGES = {self.quote(record_message)} " \
                         f"WHERE ID_USER = {self.quote(user_id)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def current_category(self, id_parent: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_category(id_parent)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_category', os.environ["EMAIL"], str(e))

    async def execute_current_category(self, id_parent: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT ID, NAME_CATEGORY, SORT_CATEGORY FROM CATEGORY " \
                           f"WHERE PARENT_ID = '{id_parent}' "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            return row_table

    async def text_category(self, id_category: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_text_category(id_category)
        except Exception as e:
            await send_message('Ошибка запроса в методе text_category', os.environ["EMAIL"], str(e))

    async def execute_text_category(self, id_category: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT NAME_CATEGORY FROM CATEGORY " \
                           f"WHERE ID = '{id_category}' "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchone()
            return row_table[0]

    async def current_nomenclature(self, id_parent: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_nomenclature(id_parent)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_current_nomenclature(self, id_parent: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT ID, NAME_NOMENCLATURE, SORT_NOMENCLATURE, PHOTO_NOMENCLATURE " \
                               f"FROM NOMENCLATURE " \
                               f"WHERE CATEGORY_ID = '{id_parent}' AND VISIBILITY_NOMENCLATURE = '1' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            return self.assembling_nomenclatures(row_table)

    async def current_description(self, kod_nomenclature: str) -> dict:
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_description(kod_nomenclature)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_description', os.environ["EMAIL"], str(e))

    async def execute_current_description(self, kod_nomenclature: str) -> dict:
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT ARTICLE, BRAND, NAME_NOMENCLATURE, TYPE_NOMENCLATURE, " \
                               f"DESCRIPTION_NOMENCLATURE, SPECIFICATION_NOMENCLATURE, PHOTO_NOMENCLATURE, " \
                               f"AVAILABILITY_NOMENCLATURE, PRICE_NOMENCLATURE, DEALER_NOMENCLATURE, " \
                               f"DISTRIBUTOR_NOMENCLATURE " \
                               f"FROM NOMENCLATURE " \
                               f"WHERE ID = '{kod_nomenclature}' AND VISIBILITY_NOMENCLATURE = '1' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchone()
            dict_nomenclature = {'ARTICLE': row_table[0], 'BRAND': row_table[1], 'NAME_NOMENCLATURE': row_table[2],
                                 'TYPE_NOMENCLATURE': row_table[3], 'DESCRIPTION_NOMENCLATURE': row_table[4],
                                 'SPECIFICATION_NOMENCLATURE': row_table[5], 'PHOTO_NOMENCLATURE': row_table[6],
                                 'AVAILABILITY_NOMENCLATURE': row_table[7], 'PRICE_NOMENCLATURE': row_table[8],
                                 'DEALER_NOMENCLATURE': row_table[9], 'DISTRIBUTOR_NOMENCLATURE': row_table[10]}
            return dict_nomenclature

    async def search_in_base_article(self, search_text: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_search_in_base_article(search_text)
        except Exception as e:
            await send_message('Ошибка запроса в методе search_in_base_article', os.environ["EMAIL"], str(e))

    async def execute_search_in_base_article(self, search_text: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT ID, NAME_NOMENCLATURE, SORT_NOMENCLATURE, PHOTO_NOMENCLATURE " \
                               f"FROM NOMENCLATURE " \
                               f"WHERE ARTICLE_CHANGE LIKE '%{search_text}%' AND VISIBILITY_NOMENCLATURE = '1' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            return set(row_table)

    async def search_in_base_name(self, search_text: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_search_in_base_name(search_text)
        except Exception as e:
            await send_message('Ошибка запроса в методе search_in_base_name', os.environ["EMAIL"], str(e))

    async def execute_search_in_base_name(self, search_text: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT ID, NAME_NOMENCLATURE, SORT_NOMENCLATURE, PHOTO_NOMENCLATURE " \
                               f"FROM NOMENCLATURE " \
                               f"WHERE NAME_NOMENCLATURE LIKE '%{search_text}%' AND VISIBILITY_NOMENCLATURE = '1' "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            return set(row_table)

    async def current_basket(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_basket(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_basket', os.environ["EMAIL"], str(e))

    async def execute_current_basket(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_basket = f"SELECT * FROM BASKET WHERE Id_user = {self.quote(id_user)} "
            await cursor.execute(sql_basket)
            basket = await cursor.fetchall()
            if len(basket) == 0:
                return None
            else:
                return self.assembling_basket(basket)

    async def current_basket_for_xlsx(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_basket_for_xlsx(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_basket_for_xlsx', os.environ["EMAIL"], str(e))

    async def execute_current_basket_for_xlsx(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_basket = f"SELECT * FROM BASKET WHERE Id_user = {self.quote(id_user)} "
            await cursor.execute(sql_basket)
            basket = await cursor.fetchall()
            if len(basket) == 0:
                return None
            else:
                return self.get_basket_dict_for_xlsx(basket)

    async def current_amount_basket(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_current_amount_basket(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе current_amount_basket', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе current_sum_basket', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе current_nomenclature_basket', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе add_basket_nomenclature', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе update_basket_nomenclature', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе delete_nomenclature_basket', os.environ["EMAIL"], str(e))

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
            await send_message('Ошибка запроса в методе clean_basket', os.environ["EMAIL"], str(e))

    async def execute_clean_basket(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_delete = f"DELETE FROM BASKET WHERE Id_user = {self.quote(id_user)}"
            await cursor.execute(sql_delete)
            await self.conn.commit()

    async def record_new_order(self, id_user: int, type_delivery: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_new_order(id_user, type_delivery)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_new_order', os.environ["EMAIL"], str(e))

    async def execute_record_new_order(self, id_user: int, type_delivery: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"INSERT INTO [ORDER_USER] " \
                         f"([Id_user], [Id_order], [Status], [Messages_by_admin], [Order_XLS], [Score], " \
                         f"[Type_delivery], [Kind_transport_company], [Comment], [Content], [INN_company], " \
                         f"[Name_company], [Email_company], [Telephone_company]) " \
                         f"VALUES ('{id_user}', " \
                         f"'', " \
                         f"'New', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'{type_delivery}', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'', " \
                         f"'') "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_type_delivery(self, id_user: int, type_delivery: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_type_delivery(id_user, type_delivery)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_type_delivery', os.environ["EMAIL"], str(e))

    async def execute_record_order_type_delivery(self, id_user: int, type_delivery: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Type_delivery = '{type_delivery}'," \
                         f"Kind_transport_company = ''," \
                         f"Comment = ''," \
                         f"Content = '', " \
                         f"INN_company = '', " \
                         f"Name_company = '', " \
                         f"Email_company = '', " \
                         f"Telephone_company = '' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_kind_transport_company(self, id_user: int, kind_transport_company: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_kind_transport_company(id_user, kind_transport_company)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_kind_transport_company', os.environ["EMAIL"],
                               str(e))

    async def execute_record_order_kind_transport_company(self, id_user: int, kind_transport_company: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Kind_transport_company = '{kind_transport_company}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_inn_company(self, id_user: int, inn_company: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_inn_company(id_user, inn_company)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_inn_company', os.environ["EMAIL"],
                               str(e))

    async def execute_record_order_inn_company(self, id_user: int, inn_company: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"INN_company = '{inn_company}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_name_company(self, id_user: int, name_company: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_name_company(id_user, name_company)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_name_company', os.environ["EMAIL"],
                               str(e))

    async def execute_record_order_name_company(self, id_user: int, name_company: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Name_company = '{name_company}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_email_company(self, id_user: int, email_company: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_email_company(id_user, email_company)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_email_company', os.environ["EMAIL"],
                               str(e))

    async def execute_record_order_email_company(self, id_user: int, email_company: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Email_company = '{email_company}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_telephone_company(self, id_user: int, telephone_company: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_telephone_company(id_user, telephone_company)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_telephone_company', os.environ["EMAIL"],
                               str(e))

    async def execute_record_order_telephone_company(self, id_user: int, telephone_company: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Telephone_company = '{telephone_company}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_comment_and_content(self, id_user: int, comment: str, content: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_comment_and_content(id_user, comment, content)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_comment_and_content', os.environ["EMAIL"], str(e))

    async def execute_record_order_comment_and_content(self, id_user: int, comment: str, content: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_comment = f"UPDATE ORDER_USER SET " \
                         f"Comment = '{comment}', " \
                         f"Content = '{content}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_comment)
            await self.conn.commit()

    async def record_order_comment(self, id_user: int, comment: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_comment(id_user, comment)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_comment', os.environ["EMAIL"], str(e))

    async def execute_record_order_comment(self, id_user: int, comment: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_comment = f"UPDATE ORDER_USER SET " \
                         f"Comment = '{comment}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status =  'New' "
            await cursor.execute(sql_comment)
            await self.conn.commit()

    async def record_order_xlsx(self, id_user: int, id_order: str, path_order: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_xlsx(id_user, id_order, path_order)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_xlsx', os.environ["EMAIL"], str(e))

    async def execute_record_order_xlsx(self, id_user: int, id_order: str, path_order: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Id_order = '{id_order}'," \
                         f"Order_XLS =  '{path_order}' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Status = 'New' "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def record_order_answer_admin(self, id_user: int, id_order: str, answer_admin: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_record_order_answer_admin(id_user, id_order, answer_admin)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_order_answer_admin', os.environ["EMAIL"], str(e))

    async def execute_record_order_answer_admin(self, id_user: int, id_order: str, answer_admin: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE ORDER_USER SET " \
                         f"Messages_by_admin = '{answer_admin}'," \
                         f"Status =  'Posted' " \
                         f"WHERE Id_user = {self.quote(id_user)} AND Id_order = {self.quote(id_order)} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_new_order(self, id_user: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_delete_new_order(id_user)
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_new_order', os.environ["EMAIL"], str(e))

    async def execute_delete_new_order(self, id_user: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_delete = f"DELETE FROM ORDER_USER WHERE Id_user = {self.quote(id_user)} AND Status = 'New' "
            await cursor.execute(sql_delete)
            await self.conn.commit()

    async def get_info_order_by_number(self, user_id: int, order_id: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_info_order_by_number(user_id, order_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_info_order_by_number', os.environ["EMAIL"], str(e))

    async def execute_get_info_order_by_number(self, user_id: int, order_id: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_info_order = f"SELECT Content, Comment FROM ORDER_USER " \
                               f"WHERE ID_USER = {self.quote(user_id)} " \
                               f"AND Id_order = {self.quote(order_id)} "
            await cursor.execute(sql_info_order)
            row_table = await cursor.fetchone()
            return tuple(row_table)

    async def get_info_order(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_info_order(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_info_order', os.environ["EMAIL"], str(e))

    async def execute_get_info_order(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_info_order = f"SELECT * FROM ORDER_USER " \
                            f"WHERE ID_USER = {self.quote(user_id)} AND Status = 'New' "
            await cursor.execute(sql_info_order)
            row_table = await cursor.fetchone()
            if row_table is None:
                return None
            else:
                my_table = PrettyTable()
                my_table.field_names = ["Id_user", "Id_order", "Status", "Messages_by_admin", "Order_XLS",
                                        "Score", "Type_delivery", "Kind_transport_company", "Comment", "Content",
                                        "INN_company", "Name_company", "Email_company", "Telephone_company"]
                my_table.add_row([row_table[0], row_table[1], row_table[2], row_table[3], row_table[4], row_table[5],
                                 row_table[6], row_table[7], row_table[8], row_table[9], row_table[10], row_table[11],
                                 row_table[12], row_table[13]])
                print(my_table)
            return row_table

    async def get_amount_order(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_amount_order(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_amount_order', os.environ["EMAIL"], str(e))

    async def execute_get_amount_order(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_info_order = f"SELECT * FROM ORDER_USER " \
                            f"WHERE ID_USER = {self.quote(user_id)} AND Status != 'New' "
            await cursor.execute(sql_info_order)
            row_table = await cursor.fetchall()
            new_order = []
            for item in row_table:
                if item[2] == 'Posted':
                    new_order.append(item)
            if row_table is None:
                amount_new_order = 0
            else:
                amount_new_order = len(new_order)
            return amount_new_order

    async def get_delivery_address(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_delivery_address(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_delivery_address', os.environ["EMAIL"], str(e))

    async def execute_get_delivery_address(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_order = f"SELECT Type_delivery, Kind_transport_company, Comment FROM ORDER_USER " \
                            f"WHERE ID_USER = {self.quote(user_id)} AND Status = 'New' "
            await cursor.execute(sql_arr_order)
            row_table = await cursor.fetchone()
            return row_table

    async def get_contact_user(self, user_id: int, kind_transport_company: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_contact_user(user_id, kind_transport_company)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_contact_user', os.environ["EMAIL"], str(e))

    async def execute_get_contact_user(self, user_id: int, kind_transport_company: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_contact_user = f"SELECT Id_order, Type_delivery, Kind_transport_company, Comment, Content, " \
                               f"INN_company, Name_company, Email_company, Telephone_company FROM ORDER_USER " \
                               f"WHERE ID_USER = {self.quote(user_id)} " \
                               f"AND Kind_transport_company = {self.quote(kind_transport_company)} " \
                               f"AND Status != 'New' "
            await cursor.execute(sql_contact_user)
            row_table = await cursor.fetchall()
            return row_table

    async def get_content_order_user(self, order_id: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_content_order_user(order_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_content_order_user', os.environ["EMAIL"], str(e))

    async def execute_get_content_order_user(self, order_id: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_contact_user = f"SELECT Content FROM ORDER_USER " \
                            f"WHERE Id_order = {self.quote(order_id)} "
            await cursor.execute(sql_contact_user)
            row_table = await cursor.fetchone()
            if row_table is None:
                return None
            else:
                return row_table

    async def get_comment_content_order_user(self, user_id: int):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_comment_content_order_user(user_id)
        except Exception as e:
            await send_message('Ошибка запроса в методе get_comment_content_order_user', os.environ["EMAIL"], str(e))

    async def execute_get_comment_content_order_user(self, user_id: int):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_arr_order = f"SELECT Comment, Content FROM ORDER_USER " \
                            f"WHERE ID_USER = {self.quote(user_id)} AND Status = 'New' "
            await cursor.execute(sql_arr_order)
            row_table = await cursor.fetchone()
            return list(row_table)

    async def get_news(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_get_news()
        except Exception as e:
            await send_message('Ошибка запроса в методе get_news', os.environ["EMAIL"], str(e))

    async def execute_get_news(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            date_str = datetime.date.today().strftime('%d.%m.%Y')
            sql_news = f"SELECT INFORMATION FROM NEWS " \
                       f"WHERE DATE_NEWS = '{date_str}' "
            await cursor.execute(sql_news)
            row_table = await cursor.fetchone()
            if row_table is None:
                return None
            else:
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

    @staticmethod
    def delete_element_before_value(arr: str, value: str):
        arr_element = arr.split()
        new_arr = []
        for item in arr_element:
            if item != value:
                new_arr.append(item)
            else:
                break
        return new_arr

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
    def get_basket_dict_for_xlsx(basket: list):
        basket_dict = {}
        if basket is None:
            basket_dict = {}
        else:
            for item in basket:
                basket_dict[item[1]] = [item[2], item[3]]
        return basket_dict

    @staticmethod
    def get_arr_orders(orders: str):
        if orders is None:
            arr_orders = []
        else:
            arr_orders = orders
        return arr_orders
