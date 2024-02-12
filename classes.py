import asyncio
import logging
import requests
import json
import re
import pyodbc
import os
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
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
        self.data = DATA()
        self.page_group = self.data.get_arr_numbers_group
        self.page_nomenclature = self.data.get_arr_numbers_nomenclature
        self.first_keyboard = self.data.get_first_keyboard
        self.price_keyboard = self.data.get_prices
        self.groups_keyboard = self.data.get_groups
        self.dict_description = self.data.get_description
        self.nomenclatures_keyboard = self.data.get_nomenclatures

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            self.start_message(message)
            answer = await self.answer_message(message, "Выберете, что Вас интересует",
                                               self.build_keyboard(self.first_keyboard, 2))
            await self.delete_messages(message.chat.id, message.from_user.id)
            self.record_message_start(str(answer.message_id), message.from_user.id, message.text)
            await self.timer.start(message.chat.id, message.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data == 'catalog'))
        async def send_catalog_message(callback: CallbackQuery):
            print(callback.data)
            await self.catalog(callback)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data.in_(self.price_keyboard)))
        async def send_group_message(callback: CallbackQuery):
            print(callback.data)
            await self.group(callback, self.price_keyboard[callback.data])

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data.in_(self.page_group)))
        async def send_group_message(callback: CallbackQuery):
            print(callback.data)
            await self.group_page_selection(callback)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data.in_(self.page_nomenclature)))
        async def send_group_message(callback: CallbackQuery):
            print(callback.data)
            await self.nomenclature_page_selection(callback)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data.in_(self.dict_description)))
        async def send_group_message(callback: CallbackQuery):
            print(callback.data)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data == 'back'))
        async def send_return_message(callback: CallbackQuery):
            print(callback.data)
            return_history = self.current_history(callback.from_user.id, 1)
            print(return_history)
            if return_history == 'catalog':
                await self.return_start(callback)
            elif return_history in self.page_group.keys():
                print('group')
                await self.return_catalog(callback)
            elif return_history in self.page_nomenclature.keys():
                print('nomenclature')
                await self.return_group(callback)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data == 'forward'))
        async def send_forward_message(callback: CallbackQuery):
            print(callback.data)
            if callback.message.text in self.nomenclatures_keyboard.keys():
                await self.nomenclature(callback, callback.message.text)

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def answer_text(self, message: Message, text: str):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML)

    async def edit_text(self, message: Message, text: str):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML)

    @property
    def auth_user(self):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_auth_user()
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_auth_user(self):
        with self.conn.cursor() as curs:
            sql_auth = f"SELECT [ID_USER], [HISTORY] FROM [TELEGRAMMBOT] "
            curs.execute(sql_auth)
            dict_user = {}
            for item in curs.fetchall():
                dict_user[int(item[0])] = item[1]
            return dict_user

    def description(self, kod: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_description(kod)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_description(self, kod: str):
        with self.conn.cursor() as curs:
            sql_description = f"SELECT [Фото], [Артикул], [Наименование], [Розница], [Наличие], [Описание], " \
                              f"[Характеристики] " \
                              f"FROM [Nomenclature] " \
                              f"WHERE [Код] = {int(kod)} "
            curs.execute(sql_description)
            return curs.fetchone()

    def current_history(self, id_user: int, amount_message: int):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_current_history(id_user, amount_message)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_history(self, id_user: int, amount_message: int):
        with self.conn.cursor() as curs:
            sql_current_history = f"SELECT [HISTORY] FROM [TELEGRAMMBOT] " \
                                  f"WHERE [ID_USER] = {self.quote(id_user)} "
            curs.execute(sql_current_history)
            arr_history = curs.fetchone()[0].split()
            if amount_message == 1:
                current_history = arr_history[-1]
            else:
                current_history = arr_history[-2]
            return current_history

    def record_message_start(self, id_answer: str, id_user: int, history: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_record_message_start(id_answer, id_user, history)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_message_start(self, id_answer: str, id_user: int, history: str):
        with self.conn.cursor() as curs:
            sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                         f"[HISTORY] = '{history}', " \
                         f"[MESSAGES] = '{id_answer}' " \
                         f"WHERE [ID_USER] = {self.quote(id_user)} "
            curs.execute(sql_record)
            print(f'Записали ответ: {id_answer}')
            self.conn.commit()

    def record_message(self, id_answer: str, id_user: int, history: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_record_message(id_answer, id_user, history)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_message(self, id_answer: str, id_user: int, history: str):
        with self.conn.cursor() as curs:
            sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                         f"[HISTORY] = [HISTORY] + ' ' + '{history}', " \
                         f"[MESSAGES] = '{id_answer}' " \
                         f"WHERE [ID_USER] = {self.quote(id_user)} "
            curs.execute(sql_record)
            print(f'Записали ответ: {id_answer}')
            self.conn.commit()

    def record_page(self, id_answer: str, id_user: int, history: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_record_page(id_answer, id_user, history)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_page(self, id_answer: str, id_user: int, history: str):
        with self.conn.cursor() as curs:
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
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_back_record_message(answer, id_user)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_back_record_message(self, answer: str, id_user: int):
        with self.conn.cursor() as curs:
            sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                         f"[MESSAGES] = '{answer}' " \
                         f"WHERE [ID_USER] = {self.quote(id_user)} "
            curs.execute(sql_record)
            print(f'Записали ответ: {answer}')
            self.conn.commit()

    async def delete_messages(self, chat_id: int, user_id: int):
        await self.bot.delete_messages_chat(chat_id, self.get_arr_messages(user_id))

    def get_arr_messages(self, user_id: int):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_get_arr_messages(user_id)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_arr_messages(self, user_id: int):
        with self.conn.cursor() as curs:
            sql_number_chat = f"SELECT [MESSAGES] FROM [TELEGRAMMBOT] " \
                              f"WHERE [ID_USER] = {self.quote(user_id)} "
            curs.execute(sql_number_chat)
            row_table = curs.fetchone()[0]
            return row_table.split()

    async def delete_messages_except_one(self, chat_id: int, user_id: int):
        await self.bot.delete_messages_chat(chat_id, self.get_arr_messages_except_one(user_id))

    def get_arr_messages_except_one(self, user_id: int):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_get_arr_messages_except_one(user_id)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_arr_messages_except_one(self, user_id: int):
        with self.conn.cursor() as curs:
            sql_number_chat = f"SELECT [MESSAGES] FROM [TELEGRAMMBOT] " \
                              f"WHERE [ID_USER] = {self.quote(user_id)} "
            curs.execute(sql_number_chat)
            row_table = curs.fetchone()[0]
            return row_table.split()[1:]

    def start_message(self, message: Message):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_start_message(message)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_start_message(self, message: Message):
        with self.conn.cursor() as curs:
            sql_auth = f"SELECT [ID_USER], [HISTORY], [MESSAGES], [EMAIL] FROM [TELEGRAMMBOT] " \
                       f"WHERE [ID_USER] = {self.quote(message.from_user.id)} "
            curs.execute(sql_auth)
            row_table = curs.fetchone()
            print(f'Клиент: {row_table}')
            if row_table is None:
                sql_record = f"INSERT INTO [TELEGRAMMBOT] ([ID_USER], [HISTORY], [MESSAGES], [EMAIL]) " \
                             f"VALUES ({str(message.from_user.id)}, '', {str(message.message_id)}, '') "
                curs.execute(sql_record)
                print(f'Новый клиент зашел с сообщением: {str(message.message_id)}')
                self.conn.commit()
            else:
                sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                             f"[HISTORY] = '', " \
                             f"[MESSAGES] = [MESSAGES] + ' ' + '{str(message.message_id)}' " \
                             f"WHERE [ID_USER] = {self.quote(message.from_user.id)} "
                curs.execute(sql_record)
                print(f'Клиент возобновил работу с сообщением: {str(message.message_id)}')
                self.conn.commit()

    async def return_start(self, call_back: CallbackQuery):
        await self.answer_message(call_back.message, "Выберете, что Вас интересует",
                                  self.build_keyboard(self.first_keyboard, 2))
        await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
        self.going_back(call_back.from_user.id, 1)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def return_catalog(self, call_back: CallbackQuery):
        answer = await self.answer_text(call_back.message, "Каталог товаров ROSSVIK 📖")
        await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
        arr_message = [str(answer.message_id)]
        for key, value in self.price_keyboard.items():
            menu_button = {'back': ['◀ 👈 Назад'], key: ['Далее 👉🏻 ▶']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.back_record_message(" ".join(arr_message), call_back.from_user.id)
        self.going_back(call_back.from_user.id, 2)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def return_group(self, call_back: CallbackQuery):
        number_page = self.going_back(call_back.from_user.id, 2)
        page = f'\nСтраница №{self.page_group[number_page]}'
        text_page = self.price_keyboard[self.current_history(call_back.from_user.id, 2)]
        answer = await self.answer_message(call_back.message, text_page[0] + page,
                                           self.build_keyboard(self.groups_keyboard[text_page[1]], 8))
        arr_message = [str(answer.message_id)]
        await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
        for value in self.groups_keyboard[text_page[1]][number_page][1].values():
            menu_button = {'back': ['◀ 👈 Назад'], 'forward': ['Далее 👉🏻 ▶']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.back_record_message(" ".join(arr_message), call_back.from_user.id)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    def going_back(self, user_id: int, amount_message: int):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_going_back(user_id, amount_message)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_going_back(self, user_id: int, amount_message: int):
        with self.conn.cursor() as curs:
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
            print(arr_history[-1])
            return arr_history[-1]

    async def catalog(self, call_back: CallbackQuery):
        answer = await self.edit_text(call_back.message, "Каталог товаров ROSSVIK 📖")
        arr_message = [str(answer.message_id)]
        for key, value in self.price_keyboard.items():
            menu_button = {'back': ['◀ 👈 Назад'], key: ['Далее 👉🏻 ▶']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.record_message(" ".join(arr_message), call_back.from_user.id, call_back.data)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def group(self, call_back: CallbackQuery, name_price: list):
        page = '\n' + 'Страница №1'
        answer = await self.answer_message(call_back.message, name_price[0] + page,
                                           self.build_keyboard(self.groups_keyboard[name_price[1]], 8))
        arr_message = [str(answer.message_id)]
        await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
        for value in self.groups_keyboard[name_price[1]]['group1'][1].values():
            menu_button = {'back': ['◀ 👈 Назад'], 'forward': ['Далее 👉🏻 ▶']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.record_message(" ".join(arr_message), call_back.from_user.id, call_back.data + ' ' + 'group1')
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def nomenclature(self, call_back: CallbackQuery, name_group: str):
        page = '\n' + 'Страница №1'
        answer = await self.answer_message(call_back.message, name_group + page,
                                           self.build_keyboard(self.nomenclatures_keyboard[name_group], 8))
        arr_message = [str(answer.message_id)]
        await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
        for key, value in self.nomenclatures_keyboard[name_group]['nomenclature1'][1].items():
            menu_button = {'back': ['◀ 👈 Назад'], key: ['Подробнее 🔍👀']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.record_message(" ".join(arr_message), call_back.from_user.id,
                            self.delete_whitespace(name_group) + ' ' + 'nomenclature1')
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def group_page_selection(self, call_back: CallbackQuery):
        number_page = self.page_group[call_back.data]
        group = self.price_keyboard[self.current_history(call_back.from_user.id, 2)]
        answer = await self.edit_message(call_back.message,
                                         call_back.message.text[0:-1] + number_page,
                                         self.build_keyboard(self.groups_keyboard[group[1]], 8))
        arr_message = [str(answer.message_id)]
        await self.delete_messages_except_one(call_back.message.chat.id, call_back.from_user.id)
        for value in self.groups_keyboard[group[1]][call_back.data][1].values():
            menu_button = {'back': ['◀ 👈 Назад'], 'forward': ['Далее 👉🏻 ▶']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.record_page(" ".join(arr_message), call_back.from_user.id, call_back.data)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def nomenclature_page_selection(self, call_back: CallbackQuery):
        number_page = self.page_nomenclature[call_back.data]
        group = call_back.message.text.split('\n')[0]
        answer = await self.edit_message(call_back.message,
                                         call_back.message.text[0:-1] + number_page,
                                         self.build_keyboard(self.nomenclatures_keyboard[group], 8))
        arr_message = [str(answer.message_id)]
        await self.delete_messages(call_back.message.chat.id, call_back.from_user.id)
        for key, value in self.nomenclatures_keyboard[group]['nomenclature1'][1].items():
            menu_button = {'back': ['◀ 👈 Назад'], key: ['Подробнее 🔍👀']}
            item_message = await self.answer_message(answer, value[0], self.build_keyboard(menu_button, 2))
            arr_message.append(str(item_message.message_id))
        self.record_page(" ".join(arr_message), call_back.from_user.id, call_back.data)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    def build_keyboard(self, dict_button: dict, column: int, dict_return_button=None):
        keyboard = self.build_menu(self.get_list_keyboard_button(dict_button), column,
                                   footer_buttons=self.get_list_keyboard_button(dict_return_button))
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_list_keyboard_button(dict_button: dict):
        button_list = []
        if dict_button:
            for key, value in dict_button.items():
                button_list.append(InlineKeyboardButton(text=value[0], callback_data=key))
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

    async def start(self, chat: int, user):
        if user in self.t.keys():
            self.t[user].cancel()
            self.t.pop(user)
            self.t[user] = asyncio.create_task(self.clean_chat(chat, user))
            await self.t[user]
        else:
            self.t[user] = asyncio.create_task(self.clean_chat(chat, user))
            await self.t[user]

    async def clean_chat(self, chat: int, user):
        await asyncio.sleep(self._clean_time)
        await self.parent.delete_messages(chat, user)
        print(f'Очищен чат у клиента {user}')
        self.clean_timer(user)

    def clean_timer(self, user: str):
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
        self.arr_numbers_group = {}
        self.arr_numbers_nomenclature = {}
        self.first_keyboard = {'news': ['Новости 📣🌐💬'], 'exchange': ['Курс валют 💰💲'],
                               'catalog': ['Каталог🛒🧾👀']}
        self.price = {'equipment': ['Оборудование для автосервиса ⛓🚗', 'Оборудование для автосервиса'],
                      'extruders': ['Вулканизаторы и экструдеры 🗜🔌', 'Вулканизаторы и экструдеры'],
                      'repair': ['Расходные материалы и инструмент для ремонта шин ‍✂⚒',
                                 'Расходные материалы и инструмент для шиноремонта'],
                      'tools': ['Слесарно-монтажный инструмент 🔧', 'Слесарно-монтажный инструмент'],
                      'air': ['Оборудование для подготовки воздуха  и пневмолинии 💨💧', 'Подготовка воздуха'],
                      'thorns': ['Ремонтные комплекты дошиповки 🌵', 'Шипы ремонтные'],
                      'part': ['Запчасти для оборудования 🧩📋📐', 'Запчасти']}
        self.conn = None

    @property
    def get_arr_numbers_group(self):
        for i in range(100):
            self.arr_numbers_group['group' + str(i)] = str(i)
        return self.arr_numbers_group

    @property
    def get_arr_numbers_nomenclature(self):
        for i in range(100):
            self.arr_numbers_nomenclature['nomenclature' + str(i)] = str(i)
        return self.arr_numbers_nomenclature

    @property
    def get_first_keyboard(self):
        return self.first_keyboard

    @property
    def get_prices(self):
        return self.price

    @property
    def get_groups(self):
        dict_groups = {}
        for item in self.get_prices.values():
            dict_groups[item[1]] = self.groups(item[1])
        return dict_groups

    def groups(self, item_price: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_groups(item_price)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_groups(self, price: str):
        with self.conn.cursor() as curs:
            sql_group = f"SELECT DISTINCT [Уровень2], [СортировкаУровень2] FROM [Nomenclature] " \
                        f"WHERE [Уровень1] = {self.quote(price)}"
            curs.execute(sql_group)
            languages_group = []
            for item_cursor in curs.fetchall():
                if item_cursor[0] == 'Нет в каталоге' or item_cursor[0] is None:
                    continue
                else:
                    languages_group.append([item_cursor[0], item_cursor[1]])
            return self.assembling_group(languages_group, 'nomenclature')

    @property
    def arr_groups(self):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_arr_groups()
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_arr_groups(self):
        with self.conn.cursor() as curs:
            sql_group = f"SELECT DISTINCT [Уровень2] FROM [Nomenclature] "
            curs.execute(sql_group)
            arr_groups = curs.fetchall()
            return arr_groups

    @property
    def get_nomenclatures(self):
        dict_nomenclatures = {}
        for item in self.arr_groups:
            dict_nomenclatures[item[0]] = self.nomenclatures(item[0])
        return dict_nomenclatures

    def nomenclatures(self, item_group: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_nomenclatures(item_group)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_nomenclatures(self, group: str):
        with self.conn.cursor() as curs:
            sql_nomenclature = f"SELECT [Наименование], [СортировкаУровень3], [Код] FROM [Nomenclature] " \
                               f"WHERE [Уровень2] = {self.quote(group)} AND [Бренд] = 'ROSSVIK'"
            curs.execute(sql_nomenclature)
            languages_nomenclature = []
            for item_cursor in curs.fetchall():
                if item_cursor[0] == 'Нет в каталоге' or item_cursor[0] is None:
                    continue
                else:
                    languages_nomenclature.append([item_cursor[0], item_cursor[1], item_cursor[2]])
            return self.assembling_nomenclatures(languages_nomenclature)

    @property
    def get_description(self):
        dict_description = {}
        for item in self.arr_description:
            dict_description[str(item[0])] = str(item[0])
        return dict_description

    @property
    def arr_description(self):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_description()
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_description(self):
        with self.conn.cursor() as curs:
            sql_description = f"SELECT [Код] " \
                              f"FROM [Nomenclature] " \
                              f"WHERE [Бренд] = 'ROSSVIK'"
            curs.execute(sql_description)
            arr_description = curs.fetchall()
            return arr_description

    @staticmethod
    def assembling_group(arr: list, label: str):
        assembling_dict_group = {}
        dict_g = {}
        i = 1
        y = 1
        for item_group in sorted(arr, key=itemgetter(1), reverse=False):
            if i < 7:
                dict_g[label + str(i)] = [item_group[0]]
                i += 1

            else:
                assembling_dict_group['group' + str(y)] = [str(y), dict_g]
                i = 1
                dict_g = {}
                y += 1
                dict_g[label + str(i)] = [item_group[0]]
                i += 1
        assembling_dict_group['group' + str(y)] = [str(y), dict_g]
        return assembling_dict_group

    @staticmethod
    def assembling_nomenclatures(arr: list):
        assembling_dict_group = {}
        dict_g = {}
        i = 1
        y = 1
        for item_group in sorted(arr, key=itemgetter(1), reverse=False):
            if i < 7:
                dict_g[str(item_group[2])] = [item_group[0]]
                i += 1

            else:
                assembling_dict_group['nomenclature' + str(y)] = [str(y), dict_g]
                i = 1
                dict_g = {}
                y += 1
                dict_g[str(item_group[2])] = [item_group[0]]
                i += 1
        assembling_dict_group['nomenclature' + str(y)] = [str(y), dict_g]
        return assembling_dict_group

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"
