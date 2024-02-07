import asyncio
import logging
import requests
import json
import re
import pyodbc
import os
from typing import Optional
from random import randint
from operator import itemgetter
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode

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
        self.dict_first_keyboard = {'Новости': ['Новости', 1], 'Курс валют': ['Курс валют', 2],
                                    'Каталог': ['Каталог', 3]}
        self.user_data = {}
        self.button = {'-2': ['change', -2], '-1': ['change', -1], '1': ['change', 1], '2': ['change', 2],
                       'Подтвердить': ['finish', 0]}
        self.bot = parent

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            self.start_message(message)
            answer = await self.answer_message(message, "Выберете, что Вас интересует",
                                               self.build_keyboard(self.dict_first_keyboard, 2))
            await self.delete_messages(message.chat.id, message.from_user.id)
            self.record_message(answer, message.from_user.id, message.text, 0)
            await self.timer.start(message.chat.id, message.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.auth_user))
        async def send_select_message(callback: CallbackQuery):
            print(callback.data)
            await self.selected_button(callback)

        @self.message(Command("random"))
        async def cmd_random(message: Message):
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Нажми меня", callback_data="random_value"))
            await message.answer("Нажмите на кнопку, чтобы бот отправил число от 1 до 10",
                                 reply_markup=builder.as_markup())

        @self.callback_query(F.data == "random_value")
        async def send_random_value(callback: CallbackQuery):
            await callback.message.answer(str(randint(1, 10)))
            await callback.answer(
                text="Спасибо, что воспользовались ботом!",
                show_alert=False)

        @self.message(Command("numbers_fab"))
        async def cmd_numbers_fab(message: Message):
            self.user_data[message.from_user.id] = 0
            await message.answer("Укажите число: 0", reply_markup=self.get_keyboard(self.button, 4,
                                                                                    footer_buttons={
                                                                                        'Назад': ['return', 0]}))

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

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

    async def selected_button(self, call_back):
        if call_back.data == 'Каталог':
            await self.catalog(call_back)
        elif call_back.data in (self.catalog_button.keys()):
            print(f'группа: {call_back.data}')

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

    async def catalog(self, call_back):
        answer = await self.edit_message(call_back.message, "Каталог товаров ROSSVIK 📖",
                                         self.build_keyboard(self.catalog_button, 1))
        self.record_message(answer, call_back.from_user.id, call_back.data, 1)
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
            for item in sorted(curs_table, key=itemgetter(1), reverse=False):
                if item[0] == 'Нет в каталоге' or item[0] is None:
                    continue
                else:
                    dict_user[self.get_key_for_callback(item[0])] = [item[0], item[1]]
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
                button_list.append(InlineKeyboardButton(text=f"{value[0]}",
                                                        callback_data=f"{key}"))
        else:
            button_list = None
        return button_list

    @staticmethod
    def get_key_for_callback(key: str):
        if len(key) > 32:
            callback_key = key[0:32]
        else:
            callback_key = key
        return callback_key

    @staticmethod
    def get_keyboard(buttons, n_cols, header_buttons=None, footer_buttons=None):
        builder = InlineKeyboardBuilder()
        for key, value in buttons.items():
            builder.button(text=key, callback_data=NumbersCallbackFactory(action=value[0], value=value[1]))
        builder.adjust(n_cols)
        if header_buttons:
            for key, value in header_buttons.items():
                builder.button(text=key, callback_data=NumbersCallbackFactory(action=value[0], value=value[1]))
                builder.adjust(4)
        if footer_buttons:
            for key, value in footer_buttons.items():
                builder.button(text=key, callback_data=NumbersCallbackFactory(action=value[0], value=value[1]))
        return builder.as_markup()

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
    def add_record(record: str, text: str):
        arr_record = record.split()
        arr_record.append(text)
        return ' '.join(arr_record)

    @staticmethod
    def format_text(text_message):
        return f'<b>{text_message}</b>'

    @staticmethod
    # Функция для оборота переменных для запроса
    def quote(request):
        return f"'{str(request)}'"


class NumbersCallbackFactory(CallbackData, prefix="rossvik"):
    action: str
    value: Optional[int] = None


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
