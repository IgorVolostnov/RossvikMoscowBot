import asyncio
import logging
import requests
import json
import re
import os
import sqlite3
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.media_group import MediaGroupBuilder
from operator import itemgetter

logging.basicConfig(level=logging.INFO)


class BotTelegram:
    def __init__(self, token_from_telegram):
        self.bot = BotMessage(token_from_telegram)
        self.dispatcher = DispatcherMessage(self.bot)
        self.list_emoji_numbers = {1: '1⃣', 2: '2⃣', 3: '3⃣', 4: '4⃣', 5: '5⃣', 6: '6⃣', 7: '7⃣', 8: 'м', 9: '9⃣',
                                   10: '🔟'}
        self.data = Currency()
        self.list_currency = {}
        self.conn = None

    async def start_dispatcher(self):
        await self.dispatcher.start_polling(self.bot)

    def run(self):
        asyncio.run(self.start_dispatcher())


class BotMessage(Bot):
    def __init__(self, token, **kw):
        Bot.__init__(self, token, **kw)

    async def delete_messages_chat(self, chat_id: int, list_message: list):
        await self.delete_messages(chat_id=chat_id, message_ids=list_message)


class DispatcherMessage(Dispatcher):
    def __init__(self, parent, **kw):
        Dispatcher.__init__(self, **kw)
        self.timer = TimerClean(self, 300)
        self.bot = parent
        self.arr_auth_user = self.auth_user
        self.data = DATA()
        self.first_keyboard = self.data.get_first_keyboard
        self.price_keyboard = self.data.get_prices
        self.category = self.data.get_category

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            answer = await self.start(message)
            if self.start_message(message):
                self.restart_record(message)
                self.add_element_message(message.from_user.id, message.message_id)
            else:
                self.start_record_new_user(message)
            await self.delete_messages(message.from_user.id)
            self.add_element_message(message.from_user.id, answer.message_id)
            await self.timer.start(message.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'catalog'))
        async def send_catalog_message(callback: CallbackQuery):
            await self.catalog(callback)
            self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.category)))
        async def send_next_category(callback: CallbackQuery):
            if await self.next_category(callback):
                self.add_element_history(callback.from_user.id, callback.data)
            else:
                self.add_element_history(callback.from_user.id, callback.data + ' ' + 'Стр.1')
            await self.timer.start(callback.from_user.id)

        # @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.price_keyboard)))
        # async def send_group_message(callback: CallbackQuery):
        #     await self.group(callback, self.price_keyboard[callback.data])

        # @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.page_group)))
        # async def send_group_message(callback: CallbackQuery):
        #     await self.group_page_selection(callback)

        # @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.page_nomenclature)))
        # async def send_group_message(callback: CallbackQuery):
        #     await self.nomenclature_page_selection(callback)

        # @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_description)))
        # async def send_description_message(callback: CallbackQuery):
        #     await self.description_nomenclature(callback)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'back'))
        async def send_return_message(callback: CallbackQuery):
            current = self.delete_element_history(callback.from_user.id)
            if current == '/start':
                await self.return_start(callback)
                await self.timer.start(callback.from_user.id)
            elif current == 'catalog':
                await self.catalog(callback)
                await self.timer.start(callback.from_user.id)
            elif current in self.category:
                await self.return_category(callback, current)
                await self.timer.start(callback.from_user.id)

            # elif return_history in self.page_group.keys():
            #     await self.return_catalog(callback)
            # elif return_history in self.page_nomenclature.keys():
            #     await self.return_group(callback)
            # elif return_history in self.dict_description.keys():
            #     await self.return_nomenclature(callback)

        # @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'forward'))
        # async def send_forward_message(callback: CallbackQuery):
        #     if callback.message.text in self.nomenclatures_keyboard.keys():
        #         await self.nomenclature(callback, callback.message.text)

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def answer_text(self, message: Message, text: str):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML)

    async def edit_text(self, message: Message, text: str):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML)

    async def send_photo(self, message: Message, photo: str, text: str):
        print(photo)
        media_group = MediaGroupBuilder(caption=text)
        if photo:
            arr_photo = photo.split()
        else:
            arr_photo = ["https://www.rossvik.moscow/images/no_foto.png"]
        for item in arr_photo:
            media_group.add_photo(media=item, parse_mode=ParseMode.HTML)
        return await self.bot.send_media_group(chat_id=message.chat.id, media=media_group.build())

    async def start(self, message: Message):
        return await self.answer_message(message, "Выберете, что Вас интересует",
                                         self.build_keyboard(self.first_keyboard, 2))

    async def catalog(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        return await self.edit_message(call_back.message,
                                       "Каталог товаров ROSSVIK 📖",
                                       self.build_keyboard(self.price_keyboard, 1, menu_button))

    async def return_start(self, call_back: CallbackQuery):
        await self.edit_message(call_back.message, "Выберете, что Вас интересует",
                                self.build_keyboard(self.first_keyboard, 2))

    async def next_category(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        current_category = self.current_category(call_back.data)
        if current_category:
            await self.edit_message(call_back.message,
                                    self.text_category(call_back.data),
                                    self.build_keyboard(current_category, 1, menu_button))
            return True
        else:
            await self.list_nomenclature(call_back)
            return False

    async def return_category(self, call_back: CallbackQuery, current_history):
        menu_button = {'back': '◀ 👈 Назад'}
        current_category = self.current_category(current_history)
        if current_category:
            return await self.edit_message(call_back.message,
                                           self.text_category(current_history),
                                           self.build_keyboard(current_category, 1, menu_button))
        else:
            new_current = self.delete_element_history(call_back.from_user.id)
            if new_current == 'catalog':
                menu_button = {'back': '◀ 👈 Назад'}
                answer = await self.edit_message(call_back.message,
                                                 "Каталог товаров ROSSVIK 📖",
                                                 self.build_keyboard(self.price_keyboard, 1, menu_button))
                await self.delete_messages(call_back.from_user.id, answer.message_id)
            else:
                current_category = self.current_category(new_current)
                answer = await self.edit_message(call_back.message,
                                                 self.text_category(new_current),
                                                 self.build_keyboard(current_category, 1, menu_button))
                await self.delete_messages(call_back.from_user.id, answer.message_id)

    async def list_nomenclature(self, call_back: CallbackQuery):
        current_nomenclature = self.current_nomenclature(call_back.data)
        pages = {}
        for page in current_nomenclature.keys():
            pages[page] = page
        heading = await self.edit_message(call_back.message, self.text_category(call_back.data),
                                          self.build_keyboard(pages, 5))
        arr_answers = [str(heading.message_id)]
        for key, value in current_nomenclature['Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', 'key': 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(call_back.from_user.id, arr_answers)

    def current_category(self, id_parent: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_category(id_parent)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_category(self, id_parent: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_category = f"SELECT KOD, NAME_CATEGORY FROM CATEGORY " \
                       f"WHERE PARENT_ID = '{id_parent}' "
        curs.execute(sql_category)
        row_table = curs.fetchall()
        dict_category = {}
        for item in row_table:
            dict_category[item[0]] = item[1]
        return dict_category

    def current_nomenclature(self, id_parent: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_nomenclature(id_parent)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_nomenclature(self, id_parent: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_nomenclature = f"SELECT KOD, NAME FROM NOMENCLATURE " \
                           f"WHERE CATEGORY_ID = '{id_parent}' "
        curs.execute(sql_nomenclature)
        row_table = curs.fetchall()
        return self.assembling_nomenclatures(row_table)

    def text_category(self, id_category: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_text_category(id_category)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_text_category(self, id_category: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_category = f"SELECT NAME_CATEGORY FROM CATEGORY " \
                       f"WHERE KOD = '{id_category}' "
        curs.execute(sql_category)
        row_table = curs.fetchone()
        return row_table[0]

    def start_message(self, message: Message):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_start_message(message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_start_message(self, message: Message):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_auth = f"SELECT [ID_USER] FROM [TELEGRAMMBOT] " \
                   f"WHERE [ID_USER] = {self.quote(message.from_user.id)} "
        curs.execute(sql_auth)
        row_table = curs.fetchone()
        print(row_table)
        if row_table is None:
            row_table = False
        else:
            row_table = True
        return row_table

    def start_record_new_user(self, message: Message):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_start_record_new_user(message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_start_record_new_user(self, message: Message):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"INSERT INTO [TELEGRAMMBOT] ([ID_USER], [HISTORY], [MESSAGES], [EMAIL]) " \
                     f"VALUES ({str(message.from_user.id)}, '/start', {str(message.message_id)}, '') "
        curs.execute(sql_record)
        self.arr_auth_user[message.from_user.id] = '/start'
        print(f'Новый клиент {self.arr_auth_user.keys()} зашел с сообщением: {str(message.message_id)}')
        self.conn.commit()

    def restart_record(self, message: Message):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_restart_record(message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_restart_record(self, message: Message):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"HISTORY = '/start' " \
                     f"WHERE ID_USER = {self.quote(message.from_user.id)} "
        curs.execute(sql_record)
        print(f'Клиент возобновил работу с сообщением: {str(message.message_id)}')
        self.conn.commit()

    async def delete_messages(self, user_id: int, except_id_message: int = None):
        await self.bot.delete_messages_chat(user_id, self.get_arr_messages(user_id, except_id_message))
        self.clean_messages_from_base(user_id, except_id_message)

    def get_arr_messages(self, user_id: int, except_id_message: int = None):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_get_arr_messages(user_id, except_id_message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_arr_messages(self, user_id: int, except_id_message: int = None):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_number_chat = f"SELECT [MESSAGES] FROM [TELEGRAMMBOT] " \
                          f"WHERE [ID_USER] = {self.quote(user_id)} "
        curs.execute(sql_number_chat)
        row_table = curs.fetchone()[0]
        arr_messages = row_table.split()
        if except_id_message:
            arr_messages.remove(str(except_id_message))
        return arr_messages

    def clean_messages_from_base(self, user_id: int, except_id_message: int = None):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                self.execute_clean_messages_from_base(user_id, except_id_message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_clean_messages_from_base(self, user_id: int, except_id_message: int = None):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        if except_id_message:
            record_message = str(except_id_message)
        else:
            record_message = ''
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[MESSAGES] = '{record_message}' " \
                     f"WHERE [ID_USER] = {self.quote(user_id)} "
        curs.execute(sql_record)
        self.conn.commit()

    def get_info_user(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_get_info_user(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_info_user(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_auth = f"SELECT [HISTORY], [MESSAGES], [EMAIL] FROM [TELEGRAMMBOT] " \
                   f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_auth)
        row_table = curs.fetchone()
        return row_table

    def add_element_history(self, id_user: int, history: str):
        current = self.get_info_user(id_user)
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_add_history(id_user, self.add_element(current[0], history))
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_add_history(self, id_user: int, history: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[HISTORY] = '{history}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

    def delete_element_history(self, id_user: int):
        current = self.get_info_user(id_user)
        current_history = self.delete_element(current[0])
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                self.execute_delete_element_history(id_user, ' '.join(current_history))
                return current_history[-1]
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_delete_element_history(self, id_user: int, history: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[HISTORY] = '{history}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

    def add_element_message(self, id_user: int, message_id: int):
        current = self.get_info_user(id_user)
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_add_message(id_user, self.add_element(current[1], str(message_id)))
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_add_message(self, id_user: int, arr_messages: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[MESSAGES] = '{arr_messages}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

    def add_arr_messages(self, id_user: int, arr_message_id: list):
        current = self.get_info_user(id_user)
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_add_arr_messages(id_user, self.add_arr_element(current[1], arr_message_id))
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_add_arr_messages(self, id_user: int, arr_messages: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[MESSAGES] = '{arr_messages}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

    @staticmethod
    def add_element(arr: str, element: str):
        arr_history = arr.split()
        arr_history.append(element)
        return ' '.join(arr_history)

    @staticmethod
    def add_arr_element(arr: str, arr_element: list):
        arr_history = arr.split()
        for item in arr_element:
            arr_history.append(item)
        return ' '.join(arr_history)

    @staticmethod
    def delete_element(arr: str):
        arr_history = arr.split()
        arr_history.pop()
        return arr_history

    @staticmethod
    def assembling_nomenclatures(arr: list):
        assembling_dict_nomenclatures = {}
        dict_m = {}
        i = 1
        y = 1
        for item_nomenclature in sorted(arr, key=itemgetter(1), reverse=False):
            if i < 7:
                dict_m[item_nomenclature[0]] = item_nomenclature[1]
                i += 1

            else:
                assembling_dict_nomenclatures['Стр.' + str(y)] = dict_m
                i = 1
                dict_m = {}
                y += 1
                dict_m[item_nomenclature[0]] = item_nomenclature[1]
                i += 1
        assembling_dict_nomenclatures['Стр.' + str(y)] = dict_m
        return assembling_dict_nomenclatures

    # async def return_catalog(self, call_back: CallbackQuery):
    #     answer = await self.answer_text(call_back.message, "Каталог товаров ROSSVIK 📖")
    #     await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
    #     arr_message = [str(answer.message_id)]
    #     for key, value in self.price_keyboard.items():
    #         menu_button = {'back': ['◀ 👈 Назад'], key: ['Далее 👉🏻 ▶']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.back_record_message(" ".join(arr_message), call_back.from_user.id)
    #     self.going_back(call_back.from_user.id, 2)
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    # async def group(self, call_back: CallbackQuery, name_price: list):
    #     page = '\n' + 'Страница №1'
    #     answer = await self.answer_message(call_back.message, name_price[0] + page,
    #                                        self.build_keyboard(self.groups_keyboard[name_price[1]], 8))
    #     arr_message = [str(answer.message_id)]
    #     await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
    #     for value in self.groups_keyboard[name_price[1]]['group1'][1].values():
    #         menu_button = {'back': ['◀ 👈 Назад'], 'forward': ['Далее 👉🏻 ▶']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.record_message(" ".join(arr_message), call_back.from_user.id, call_back.data + ' ' + 'group1')
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)
    #
    # async def group_page_selection(self, call_back: CallbackQuery):
    #     number_page = self.page_group[call_back.data]
    #     group = self.price_keyboard[self.current_history(call_back.from_user.id, 2)]
    #     answer = await self.edit_message(call_back.message,
    #                                      call_back.message.text[0:-1] + number_page,
    #                                      self.build_keyboard(self.groups_keyboard[group[1]], 8))
    #     arr_message = [str(answer.message_id)]
    #     await self.delete_messages_except_one(call_back.message.chat.id, call_back.from_user.id)
    #     for value in self.groups_keyboard[group[1]][call_back.data][1].values():
    #         menu_button = {'back': ['◀ 👈 Назад'], 'forward': ['Далее 👉🏻 ▶']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.record_page(" ".join(arr_message), call_back.from_user.id, call_back.data)
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)
    #
    # async def return_group(self, call_back: CallbackQuery):
    #     number_page = self.going_back(call_back.from_user.id, 2)
    #     page = f'\nСтраница №{self.page_group[number_page]}'
    #     text_page = self.price_keyboard[self.current_history(call_back.from_user.id, 2)]
    #     answer = await self.answer_message(call_back.message, text_page[0] + page,
    #                                        self.build_keyboard(self.groups_keyboard[text_page[1]], 8))
    #     arr_message = [str(answer.message_id)]
    #     await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
    #     for value in self.groups_keyboard[text_page[1]][number_page][1].values():
    #         menu_button = {'back': ['◀ 👈 Назад'], 'forward': ['Далее 👉🏻 ▶']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.back_record_message(" ".join(arr_message), call_back.from_user.id)
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)
    #
    # async def nomenclature(self, call_back: CallbackQuery, name_group: str):
    #     page = '\n' + 'Страница №1'
    #     answer = await self.answer_message(call_back.message, name_group + page,
    #                                        self.build_keyboard(self.nomenclatures_keyboard[name_group], 8))
    #     arr_message = [str(answer.message_id)]
    #     await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
    #     for key, value in self.nomenclatures_keyboard[name_group]['nomenclature1'][1].items():
    #         menu_button = {'back': ['◀ 👈 Назад'], key: ['Подробнее 🔍👀']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.record_message(" ".join(arr_message), call_back.from_user.id,
    #                         self.delete_whitespace(name_group) + ' ' + 'nomenclature1')
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)
    #
    # async def nomenclature_page_selection(self, call_back: CallbackQuery):
    #     number_page = self.page_nomenclature[call_back.data]
    #     group = call_back.message.text.split('\n')[0]
    #     answer = await self.edit_message(call_back.message,
    #                                      call_back.message.text[0:-1] + number_page,
    #                                      self.build_keyboard(self.nomenclatures_keyboard[group], 8))
    #     arr_message = [str(answer.message_id)]
    #     await self.delete_messages_except_one(call_back.message.chat.id, call_back.from_user.id)
    #     for key, value in self.nomenclatures_keyboard[group][call_back.data][1].items():
    #         menu_button = {'back': ['◀ 👈 Назад'], key: ['Подробнее 🔍👀']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.record_page(" ".join(arr_message), call_back.from_user.id, call_back.data)
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)
    #
    # async def return_nomenclature(self, call_back: CallbackQuery):
    #     number_page = self.going_back(call_back.from_user.id, 1)
    #     page = f'\nСтраница №{self.page_nomenclature[number_page]}'
    #     text_page = self.create_nomenclature(self.current_history(call_back.from_user.id, 2))
    #     answer = await self.answer_message(call_back.message, text_page + page,
    #                                        self.build_keyboard(self.nomenclatures_keyboard[text_page], 8))
    #     arr_message = [str(answer.message_id)]
    #     await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
    #     for key, value in self.nomenclatures_keyboard[text_page][number_page][1].items():
    #         menu_button = {'back': ['◀ 👈 Назад'], key: ['Подробнее 🔍👀']}
    #         item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
    #         arr_message.append(str(item_message.message_id))
    #     self.back_record_message(" ".join(arr_message), call_back.from_user.id)
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)
    #
    # async def description_nomenclature(self, call_back: CallbackQuery):
    #     whitespace = '\n'
    #     arr_description = self.description(call_back.data)
    #     if arr_description[4] == "0":
    #         availability = "Нет на складе"
    #     else:
    #         availability = arr_description[4]
    #     info_nomenclature = f'Артикул: {self.format_text(arr_description[1])}{whitespace}' \
    #                         f'{self.format_text(arr_description[2])}{whitespace}' \
    #                         f'Цена: {self.format_text(arr_description[3])} RUB{whitespace}' \
    #                         f'Наличие: {self.format_text(availability)}{whitespace}'
    #     description_text = f'{arr_description[5]}{whitespace}' \
    #                        f'{arr_description[6]}'
    #     if re.sub('\W+', '', description_text) == "":
    #         description_text = "Нет подробной информации"
    #     arr_answer = await self.send_photo(call_back.message, arr_description[0], info_nomenclature)
    #     menu_button = {'back': ['◀ 👈 Назад'], 'add': ['В корзину 🛒']}
    #     answer_description = await self.answer_message(arr_answer[0], description_text,
    #                                                    self.build_keyboard(menu_button, 2))
    #     arr_answer.append(answer_description)
    #     arr_message = []
    #     for item_message in arr_answer:
    #         arr_message.append(str(item_message.message_id))
    #     await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
    #     self.record_message(" ".join(arr_message), call_back.from_user.id, call_back.data)
    #     await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    @property
    def auth_user(self):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_auth_user()
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_auth_user(self):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_auth = f"SELECT [ID_USER], [HISTORY] FROM [TELEGRAMMBOT] "
        curs.execute(sql_auth)
        dict_user = {}
        for item in curs.fetchall():
            dict_user[int(item[0])] = item[1]
        print(dict_user)
        return dict_user

    def description(self, kod: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_description(kod)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_description(self, kod: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_description = f"SELECT [Фото], [Артикул], [Наименование], [Розница], [Наличие], [Описание], " \
                          f"[Характеристики] " \
                          f"FROM [Nomenclature] " \
                          f"WHERE [Код] = {int(kod)} "
        curs.execute(sql_description)
        arr_description = curs.fetchone()
        return arr_description

    def current_history(self, id_user: int, amount_message: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_history(id_user, amount_message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_history(self, id_user: int, amount_message: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_current_history = f"SELECT [HISTORY] FROM [TELEGRAMMBOT] " \
                              f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_current_history)
        arr_history = curs.fetchone()[0].split()
        if amount_message == 1:
            current_history = arr_history[-1]
        else:
            current_history = arr_history[-2]
        print(current_history)
        return current_history

    def record_message(self, id_answer: str, id_user: int, history: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_record_message(id_answer, id_user, history)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_message(self, id_answer: str, id_user: int, history: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[HISTORY] = [HISTORY] + ' ' + '{history}', " \
                     f"[MESSAGES] = '{id_answer}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        print(f'Записали ответ: {id_answer}')
        self.conn.commit()

    def record_page(self, id_answer: str, id_user: int, history: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_record_page(id_answer, id_user, history)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_page(self, id_answer: str, id_user: int, history: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_current_history = f"SELECT [HISTORY] FROM [TELEGRAMMBOT] " \
                              f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_current_history)
        current_history = curs.fetchone()[0].split()
        current_history[-1] = history
        new_history = " ".join(current_history)
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[HISTORY] = '{new_history}', " \
                     f"[MESSAGES] = '{id_answer}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        print(f'Записали ответ: {id_answer}')
        self.conn.commit()

    def back_record_message(self, answer: str, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_back_record_message(answer, id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_back_record_message(self, answer: str, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[MESSAGES] = '{answer}' " \
                     f"WHERE [ID_USER] = {self.quote(id_user)} "
        curs.execute(sql_record)
        print(f'Записали ответ: {answer}')
        self.conn.commit()

    async def delete_messages_except_one(self, chat_id: int, user_id: int):
        await self.bot.delete_messages_chat(chat_id, self.get_arr_messages_except_one(user_id))

    def get_arr_messages_except_one(self, user_id: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_get_arr_messages_except_one(user_id)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_arr_messages_except_one(self, user_id: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_number_chat = f"SELECT [MESSAGES] FROM [TELEGRAMMBOT] " \
                          f"WHERE [ID_USER] = {self.quote(user_id)} "
        curs.execute(sql_number_chat)
        row_table = curs.fetchone()[0]
        return row_table.split()[1:]

    def going_back(self, user_id: int, amount_message: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_going_back(user_id, amount_message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_going_back(self, user_id: int, amount_message: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        return_catalog = f"SELECT [HISTORY] FROM [TELEGRAMMBOT] " \
                         f"WHERE [ID_USER] = {self.quote(user_id)} "
        curs.execute(return_catalog)
        arr_history = curs.fetchone()[0].split()
        if amount_message == 1:
            arr_history.pop()
        else:
            arr_history.pop()
            arr_history.pop()
        new_history = " ".join(arr_history)
        sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                     f"[HISTORY] = '{new_history}' " \
                     f"WHERE [ID_USER] = {self.quote(user_id)} "
        curs.execute(sql_record)
        self.conn.commit()
        return arr_history[-1]

    def build_keyboard(self, dict_button: dict, column: int, dict_return_button=None):
        keyboard = self.build_menu(self.get_list_keyboard_button(dict_button), column,
                                   footer_buttons=self.get_list_keyboard_button(dict_return_button))
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_list_keyboard_button(dict_button: dict):
        button_list = []
        if dict_button:
            for key, value in dict_button.items():
                button_list.append(InlineKeyboardButton(text=value, callback_data=key))
        else:
            button_list = None
        return button_list

    @staticmethod
    def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, [header_buttons])
        if footer_buttons:
            for item in footer_buttons:
                menu.append([item])
        return menu

    @staticmethod
    def format_text(text_message: str):
        return f'<b>{text_message}</b>'

    @staticmethod
    # Функция для оборота переменных для запроса
    def quote(request):
        return f"'{str(request)}'"

    @staticmethod
    def delete_whitespace(request: str):
        arr = request.split()
        arr_new = '///'.join(arr)
        return arr_new

    @staticmethod
    def create_nomenclature(request: str):
        arr = request.split('///')
        arr_new = ' '.join(arr)
        return arr_new


class Currency:
    def __init__(self):
        self.API_address = 'https://min-api.cryptocompare.com/data/price?'
        self.base = None
        self.quote = None
        self.amount = ""
        self.arr_currency = {'RUB': 'РУБЛЬ', 'USD': 'ДОЛЛАР', 'EUR': 'ЕВРО', 'BTC': 'БИТКОИН'}
        self.error = []

    @property
    def answer(self):
        whitespace = '\n'
        if len(self.error) == 0:
            answer = self.get_price(self.base, self.quote, self.amount)
            return answer
        else:
            answer = whitespace.join(self.error)
            self.clear()
            return answer

    @property
    def set_base(self):
        return self.base

    @set_base.setter
    def set_base(self, base):
        try:
            self.base = self.search_key(base)
            if ''.join(self.base) == '':
                raise APIException(f'Я не знаю что такое {base}...Расскажете мне об этом?')
        except APIException as e:
            self.error.append(str(e))

    @property
    def set_quote(self):
        return self.quote

    @set_quote.setter
    def set_quote(self, quote):
        try:
            self.quote = self.search_key(quote)
            if ''.join(self.quote) == '':
                raise APIException(f'{quote} cтранная какая-то Валюта...Пойду погуглю о ней')
        except APIException as e:
            self.error.append(str(e))

    @property
    def set_amount(self):
        return self.amount

    @set_amount.setter
    def set_amount(self, amount):
        try:
            self.amount = int(amount)
        except ValueError as e:
            print(e)

    def search_key(self, search_string):
        search = re.sub('\W+', '', search_string).upper()
        return ''.join([key for key, val in self.arr_currency.items() if search in val])

    def clear(self):
        self.base = None
        self.quote = None
        self.amount = 1
        self.error = []

    @staticmethod
    def get_price(base, quote, amount):
        try:
            exchange = requests.get(
                f'https://min-api.cryptocompare.com/data/price?fsym={base}&tsyms={quote}')
            if exchange.status_code == 200:
                answer = f"{str('{:.2f}'.format(float(json.loads(exchange.content)[quote]) * amount))} " \
                         f"{quote}"
                return answer
            else:
                raise APIException('Что-то наши аналитики не отвечают, может устали, попробуйте позже)))')
        except APIException as e:
            print(e)


class TimerClean:
    def __init__(self, parent, second: int):
        self.parent = parent
        self._clean_time = second
        self.t = {}

    async def start(self, user: int):
        if user in self.t.keys():
            self.t[user].cancel()
            self.t.pop(user)
            self.t[user] = asyncio.create_task(self.clean_chat(user))
            await self.t[user]
        else:
            self.t[user] = asyncio.create_task(self.clean_chat(user))
            await self.t[user]

    async def clean_chat(self, user: int):
        await asyncio.sleep(self._clean_time)
        await self.parent.delete_messages(user)
        print(f'Очищен чат у клиента {str(user)}')
        self.clean_timer(user)

    def clean_timer(self, user: int):
        self.t.pop(user)


class APIException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'Ниче не понял..., {0} '.format(self.message)
        else:
            return 'Что-то я летаю в облаках, повторите, пожалуйста!'


class TimerError(Exception):
    """Пользовательское исключение, используемое для сообщения об ошибках при использовании класса Timer"""


class DATA:
    def __init__(self):
        self.first_keyboard = {'news': 'Новости 📣🌐💬', 'exchange': 'Курс валют 💰💲',
                               'catalog': 'Каталог🛒🧾👀'}
        self.price = {'506': 'Шиноремонтные материалы ✂⚒',
                               '507': 'Вентили 🗜',
                               '556': 'Ремонтные шипы ‍🌵',
                               '552': 'Шиномонтажное оборудование 🚗🔧',
                               '600': 'Подъемное оборудование ⛓',
                               '547': 'Инструмент 🔧',
                               '608': 'Специнструмент 🛠',
                               '726': 'Заправки кондиционеров ❄',
                               '549': 'Компрессоры ⛽',
                               '597': 'Пневмоинструмент 🎣',
                               '707': 'Пневмолинии 💨💧',
                               '623': 'Расходные материалы для автосервиса 📜🚗',
                               '946': 'Моечно-уборочное оборудование 🧹',
                               '493': 'АвтоХимия ☣⚗️',
                               '580': 'Гаражное оборудование 👨🏾‍🔧',
                               '593': 'Диагностическое оборудование 🕵️‍♀',
                               '603': 'Маслосменное оборудование 💦🛢️',
                               '738': 'Электроинструмент 🔋',
                               '660': 'Сход/развалы 🔩📐',
                               '663': 'Мойки деталей 🛁',
                               '1095': 'Вытяжка отработанных газов ♨',
                               '692': 'Экспресс-сервис 🚅🤝🏻',
                               '688': 'Мебель для автосервиса 🗄️',
                               '702': 'Запчасти 🧩⚙️',
                               '1100': 'Автотовары 🍱',
                               '1101': 'Садовый инвентарь 👩‍🌾',
                               '1104': 'Акции 📢'}
        self.conn = None

    @property
    def get_first_keyboard(self):
        return self.first_keyboard

    @property
    def get_prices(self):
        return self.price

    @property
    def get_category(self):
        dict_category = {}
        for item in range(2000):
            dict_category[str(item)] = str(item)
        return dict_category
    #
    # def groups(self, item_price: str):
    #     try:
    #         connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
    #         with pyodbc.connect(connect_string) as self.conn:
    #             return self.execute_groups(item_price)
    #     except pyodbc.Error as error:
    #         print("Ошибка чтения данных из таблицы", error)
    #     finally:
    #         if self.conn:
    #             self.conn.close()
    #
    # def execute_groups(self, price: str):
    #     with self.conn.cursor() as curs:
    #         sql_group = f"SELECT DISTINCT [Уровень2], [СортировкаУровень2] FROM [Nomenclature] " \
    #                     f"WHERE [Уровень1] = {self.quote(price)}"
    #         curs.execute(sql_group)
    #         languages_group = []
    #         for item_cursor in curs.fetchall():
    #             if item_cursor[0] == 'Нет в каталоге' or item_cursor[0] is None:
    #                 continue
    #             else:
    #                 languages_group.append([item_cursor[0], item_cursor[1]])
    #         return self.assembling_group(languages_group, 'nomenclature')
    #
    # @property
    # def arr_groups(self):
    #     try:
    #         connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
    #         with pyodbc.connect(connect_string) as self.conn:
    #             return self.execute_arr_groups()
    #     except pyodbc.Error as error:
    #         print("Ошибка чтения данных из таблицы", error)
    #     finally:
    #         if self.conn:
    #             self.conn.close()
    #
    # def execute_arr_groups(self):
    #     with self.conn.cursor() as curs:
    #         sql_group = f"SELECT DISTINCT [Уровень2] FROM [Nomenclature] "
    #         curs.execute(sql_group)
    #         arr_groups = curs.fetchall()
    #         return arr_groups
    #
    # @property
    # def get_nomenclatures(self):
    #     dict_nomenclatures = {}
    #     for item in self.arr_groups:
    #         dict_nomenclatures[item[0]] = self.nomenclatures(item[0])
    #     return dict_nomenclatures
    #
    # def nomenclatures(self, item_group: str):
    #     try:
    #         connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
    #         with pyodbc.connect(connect_string) as self.conn:
    #             return self.execute_nomenclatures(item_group)
    #     except pyodbc.Error as error:
    #         print("Ошибка чтения данных из таблицы", error)
    #     finally:
    #         if self.conn:
    #             self.conn.close()
    #
    # def execute_nomenclatures(self, group: str):
    #     with self.conn.cursor() as curs:
    #         sql_nomenclature = f"SELECT [Наименование], [СортировкаУровень3], [Код] FROM [Nomenclature] " \
    #                            f"WHERE [Уровень2] = {self.quote(group)} AND [Бренд] = 'ROSSVIK'"
    #         curs.execute(sql_nomenclature)
    #         languages_nomenclature = []
    #         for item_cursor in curs.fetchall():
    #             if item_cursor[0] == 'Нет в каталоге' or item_cursor[0] is None:
    #                 continue
    #             else:
    #                 languages_nomenclature.append([item_cursor[0], item_cursor[1], item_cursor[2]])
    #         return self.assembling_nomenclatures(languages_nomenclature)
    #
    # @property
    # def get_description(self):
    #     dict_description = {}
    #     for item in self.arr_description:
    #         dict_description[str(item[0])] = str(item[0])
    #     return dict_description
    #
    # @property
    # def arr_description(self):
    #     try:
    #         connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
    #         with pyodbc.connect(connect_string) as self.conn:
    #             return self.execute_description()
    #     except pyodbc.Error as error:
    #         print("Ошибка чтения данных из таблицы", error)
    #     finally:
    #         if self.conn:
    #             self.conn.close()
    #
    # def execute_description(self):
    #     with self.conn.cursor() as curs:
    #         sql_description = f"SELECT [Код] " \
    #                           f"FROM [Nomenclature] " \
    #                           f"WHERE [Бренд] = 'ROSSVIK'"
    #         curs.execute(sql_description)
    #         arr_description = curs.fetchall()
    #         return arr_description
    #
    # @staticmethod
    # def assembling_group(arr: list, label: str):
    #     assembling_dict_group = {}
    #     dict_g = {}
    #     i = 1
    #     y = 1
    #     for item_group in sorted(arr, key=itemgetter(1), reverse=False):
    #         if i < 7:
    #             dict_g[label + str(i)] = [item_group[0]]
    #             i += 1
    #
    #         else:
    #             assembling_dict_group['group' + str(y)] = [str(y), dict_g]
    #             i = 1
    #             dict_g = {}
    #             y += 1
    #             dict_g[label + str(i)] = [item_group[0]]
    #             i += 1
    #     assembling_dict_group['group' + str(y)] = [str(y), dict_g]
    #     return assembling_dict_group
    #
    # @staticmethod
    # def assembling_nomenclatures(arr: list):
    #     assembling_dict_group = {}
    #     dict_g = {}
    #     i = 1
    #     y = 1
    #     for item_group in sorted(arr, key=itemgetter(1), reverse=False):
    #         if i < 7:
    #             dict_g[str(item_group[2])] = [item_group[0]]
    #             i += 1
    #
    #         else:
    #             assembling_dict_group['nomenclature' + str(y)] = [str(y), dict_g]
    #             i = 1
    #             dict_g = {}
    #             y += 1
    #             dict_g[str(item_group[2])] = [item_group[0]]
    #             i += 1
    #     assembling_dict_group['nomenclature' + str(y)] = [str(y), dict_g]
    #     return assembling_dict_group
    #
    # @staticmethod
    # def quote(request):
    #     return f"'{str(request)}'"
