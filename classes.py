import asyncio
import logging
import requests
import json
import re
import pyodbc
import os
from operator import itemgetter
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
from dict_menu import menu_button, price

logging.basicConfig(level=logging.INFO)


class BotTelegram:
    def __init__(self, token_from_telegram):
        self.bot = BotMessage(token_from_telegram)
        self.dispatcher = DispatcherMessage(self.bot)
        self.list_amount = {"/1": "1", "/2": "2", "/3": "3", "/4": "4", "/5": "5", "/6": "6", "/7": "7", "/8": "8",
                            "/9": "9", "/0": "0"}
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
        self.dict_first_keyboard = {'news': ['Новости 📣🌐💬'], 'exchange': ['Курс валют 💰💲'],
                                    'catalog': ['Каталог🛒🧾👀']}
        self.menu_button = menu_button
        self.item_catalog = price
        self.bot = parent

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            self.start_message(message)
            answer = await self.answer_message(message, "Выберете, что Вас интересует",
                                               self.build_keyboard(self.dict_first_keyboard, 2))
            await self.delete_messages(message.chat.id, message.from_user.id)
            self.record_message(answer, message.from_user.id, message.text, 0)
            await self.timer.start(message.chat.id, message.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data == 'back'))
        async def send_return_message(callback: CallbackQuery):
            return_history = self.going_back(callback.from_user.id)
            if return_history == '/start':
                await self.return_start(callback)
            elif return_history == 'catalog':
                await self.return_catalog(callback)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data == 'catalog'))
        async def send_catalog_message(callback: CallbackQuery):
            print(callback.data)
            await self.catalog(callback)

        @self.callback_query(F.from_user.id.in_(self.auth_user) & (F.data.in_(self.catalog_button)))
        async def send_group_message(callback: CallbackQuery):
            await self.group(callback, self.catalog_button[callback.data][1])

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

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

    def record_message(self, answer: Message, id_user, text: str, amount: int):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_record_answer(answer, id_user, text, amount)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_answer(self, answer: Message, id_user, text: str, amount_messages: int):
        with self.conn.cursor() as curs:
            if amount_messages == 0:
                sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                             f"[HISTORY] = '{text}', " \
                             f"[MESSAGES] = '{str(answer.message_id)}' " \
                             f"WHERE [ID_USER] = {self.quote(id_user)} "
            elif amount_messages == 1:
                sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                             f"[HISTORY] = [HISTORY] + ' ' + '{text}', " \
                             f"[MESSAGES] = '{str(answer.message_id)}' " \
                             f"WHERE [ID_USER] = {self.quote(id_user)} "
            else:
                sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                             f"[HISTORY] = [HISTORY] + ' ' + '{text}', " \
                             f"[MESSAGES] = [MESSAGES] + ' ' + '{text}' " \
                             f"WHERE [ID_USER] = {self.quote(id_user)} "
            curs.execute(sql_record)
            print(f'Записали ответ: {str(answer.message_id)}')
            self.conn.commit()

    async def delete_messages(self, chat_id: int, user_id):
        await self.bot.delete_messages_chat(chat_id, self.get_arr_messages(user_id))

    def get_arr_messages(self, user_id):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_get_arr_messages(user_id)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_arr_messages(self, user_id):
        with self.conn.cursor() as curs:
            sql_number_chat = f"SELECT [MESSAGES] FROM [TELEGRAMMBOT] " \
                       f"WHERE [ID_USER] = {self.quote(user_id)} "
            curs.execute(sql_number_chat)
            row_table = curs.fetchone()[0]
            return row_table.split()

    async def return_start(self, call_back):
        await self.edit_message(call_back.message, "Выберете, что Вас интересует",
                                self.build_keyboard(self.dict_first_keyboard, 2))
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    def start_message(self, message):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_start_message(message)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_start_message(self, message):
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

    def going_back(self, user_id):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_going_back(user_id)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_going_back(self, user_id):
        with self.conn.cursor() as curs:
            return_catalog = f"SELECT [HISTORY] FROM [TELEGRAMMBOT] " \
                              f"WHERE [ID_USER] = {self.quote(user_id)} "
            curs.execute(return_catalog)
            arr_history = curs.fetchone()[0].split()
            arr_history.pop()
            new_history = " ".join(arr_history)
            sql_record = f"UPDATE [TELEGRAMMBOT] SET " \
                         f"[HISTORY] = '{new_history}' " \
                         f"WHERE [ID_USER] = {self.quote(user_id)} "
            curs.execute(sql_record)
            self.conn.commit()
            print(arr_history[len(arr_history)-1])
            return arr_history[len(arr_history)-1]

    async def catalog(self, call_back):
        answer = await self.edit_text(call_back.message, "Каталог товаров ROSSVIK 📖")
        for key, price in self.item_catalog.items():
            await self.answer_message(answer, price[0], self.build_keyboard(self.menu_button, 2))
        # await self.delete_messages(call_back.message.chat.id, call_back.message.from_user.id)
        self.record_message(answer, call_back.from_user.id, call_back.data, 1)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def return_catalog(self, call_back):
        await self.edit_message(call_back.message, "Каталог товаров ROSSVIK 📖",
                                self.build_keyboard(self.catalog_button, 1, {'Назад': ['Назад']}))
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    @property
    def catalog_button(self):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_catalog_button()
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_catalog_button(self):
        with self.conn.cursor() as curs:
            sql_price = f"SELECT DISTINCT [Уровень1], [СортировкаУровень1] FROM [Nomenclature] "
            curs.execute(sql_price)
            curs_table = curs.fetchall()
            dict_user = {}
            i = 1
            for item in sorted(curs_table, key=itemgetter(1), reverse=False):
                if item[0] == 'Нет в каталоге' or item[0] is None:
                    continue
                else:
                    dict_user[str(i)] = [item[0]]
                    i += 1
            return dict_user

    async def group(self, call_back, name_group: str):
        answer = await self.edit_message(call_back.message, name_group,
                                         self.build_keyboard(self.group_button(name_group), 1, {'Назад': ['Назад']}))
        self.record_message(answer, call_back.from_user.id, call_back.data, 1)
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    async def return_group(self, call_back, name_group: str):
        await self.edit_message(call_back.message, name_group,
                                self.build_keyboard(self.group_button(name_group), 1, {'Назад': ['Назад']}))
        await self.timer.start(call_back.message.chat.id, call_back.from_user.id)

    def group_button(self, data_price: str):
        try:
            connect_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=\\' + f'{os.getenv("CONNECTION")}'
            with pyodbc.connect(connect_string) as self.conn:
                return self.execute_group_button(data_price)
        except pyodbc.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_group_button(self, data_price: str):
        with self.conn.cursor() as curs:
            sql_group = f"SELECT DISTINCT [Уровень2], [СортировкаУровень2] FROM [Nomenclature] " \
                        f"WHERE [Уровень1] = {self.quote(data_price)}"
            curs.execute(sql_group)
            curs_table = curs.fetchall()
            dict_user = {}
            i = 1
            for item in sorted(curs_table, key=itemgetter(1), reverse=False):
                if item[0] == 'Нет в каталоге' or item[0] is None:
                    continue
                else:
                    dict_user[str(i)] = [item[0]]
                    i += 1
            return dict_user

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
            self.error.append('Я наверное плохо рассказал, как у нас тут всё работает. Сначала валюта, '
                              'которую переводим, потом в какую переводим, '
                              'а затем какое количество в виде ЦЕЛОГО ЧИСЛА)))')

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
            price = requests.get(
                f'https://min-api.cryptocompare.com/data/price?fsym={base}&tsyms={quote}')
            if price.status_code == 200:
                answer = f"{str('{:.2f}'.format(float(json.loads(price.content)[quote]) * amount))} " \
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
