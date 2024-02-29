import asyncio
import logging
import requests
import json
import re
import os
import sqlite3
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
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

    async def alert_message(self, id_call_back: str, text: str):
        await self.answer_callback_query(id_call_back, text=text, show_alert=True)


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
        self.pages = self.data.get_pages
        self.nomenclatures = self.data.get_nomenclature
        self.button_calculater = self.data.get_button_calculater

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

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages)))
        async def send_next_page(callback: CallbackQuery):
            if await self.next_page(callback):
                self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.nomenclatures)))
        async def send_description(callback: CallbackQuery):
            await self.description(callback)
            self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'add'))
        async def send_basket(callback: CallbackQuery):
            await self.add_nomenclature(callback)
            self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.button_calculater)))
        async def send_change_amount(callback: CallbackQuery):
            await self.change_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'minus'))
        async def send_change_minus(callback: CallbackQuery):
            await self.minus_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'plus'))
        async def send_change_plus(callback: CallbackQuery):
            await self.plus_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'delete'))
        async def send_change_delete(callback: CallbackQuery):
            await self.delete_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'done'))
        async def send_done_basket(callback: CallbackQuery):
            await self.add_to_basket(callback)
            self.delete_element_history(callback.from_user.id)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'basket'))
        async def send_show_basket(callback: CallbackQuery):
            await self.show_basket(callback)
            self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

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
            elif current in self.pages:
                await self.return_page(callback, current)
                self.add_element_history(callback.from_user.id, current)
                await self.timer.start(callback.from_user.id)
            elif current in self.nomenclatures:
                await self.return_description(callback, current)
                await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'back_basket'))
        async def send_return_message(callback: CallbackQuery):
            current = self.delete_element_history(callback.from_user.id)
            if current in self.nomenclatures:
                await self.description(callback, current)
                await self.timer.start(callback.from_user.id)
            elif current == 'add':
                previous_history = self.previous_history(callback.from_user.id)
                await self.add_nomenclature_from_basket(callback, previous_history)
                await self.timer.start(callback.from_user.id)

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def send_photo(self, message: Message, photo: str, text: str):
        media_group = MediaGroupBuilder(caption=text)
        if photo:
            arr_photo = photo.split()[:10]
        else:
            arr_photo = ["https://www.rossvik.moscow/images/no_foto.png"]
        for item in arr_photo:
            media_group.add_photo(media=item, parse_mode=ParseMode.HTML)
        try:
            return await self.bot.send_media_group(chat_id=message.chat.id, media=media_group.build())
        except TelegramBadRequest as error:
            media_group = MediaGroupBuilder(caption=text)
            arr_photo = ["https://www.rossvik.moscow/images/no_foto.png"]
            for item in arr_photo:
                media_group.add_photo(media=item, parse_mode=ParseMode.HTML)
            return await self.bot.send_media_group(chat_id=message.chat.id, media=media_group.build())

    async def start(self, message: Message):
        return await self.answer_message(message, "Выберете, что Вас интересует",
                                         self.build_keyboard(self.first_keyboard, 2))

    async def return_start(self, call_back: CallbackQuery):
        await self.edit_message(call_back.message, "Выберете, что Вас интересует",
                                self.build_keyboard(self.first_keyboard, 2))

    async def catalog(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        return await self.edit_message(call_back.message,
                                       "Каталог товаров ROSSVIK 📖",
                                       self.build_keyboard(self.price_keyboard, 1, menu_button))

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

    async def next_page(self, call_back: CallbackQuery):
        if self.pages[call_back.data] == call_back.message.text[-1]:
            return False
        else:
            id_category = self.delete_element_history(call_back.from_user.id)
            current_nomenclature = self.current_nomenclature(id_category)
            pages = {}
            for page in current_nomenclature.keys():
                pages[page] = page
            heading = await self.edit_message(call_back.message,
                                              call_back.message.text[:-1] + self.pages[call_back.data],
                                              self.build_keyboard(pages, 5))
            await self.delete_messages(call_back.from_user.id, heading.message_id)
            arr_answers = []
            for key, value in current_nomenclature[call_back.data].items():
                menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
                answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            self.add_arr_messages(call_back.from_user.id, arr_answers)
            return True

    async def return_page(self, call_back: CallbackQuery, current_page: str):
        number_page = '\n' + 'Страница №' + self.pages[current_page]
        id_category = self.delete_element_history(call_back.from_user.id)
        current_nomenclature = self.current_nomenclature(id_category)
        text = self.text_category(id_category)
        pages = {}
        for page in current_nomenclature.keys():
            pages[page] = page
        heading = await self.edit_message(call_back.message, text + number_page, self.build_keyboard(pages, 5))
        await self.delete_messages(call_back.from_user.id, heading.message_id)
        await asyncio.sleep(0.5)
        arr_answers = []
        for key, value in current_nomenclature[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(call_back.from_user.id, arr_answers)
        return True

    async def description(self, call_back: CallbackQuery, id_nomenclature: str = None):
        if id_nomenclature:
            current_description = await self.description_nomenclature(id_nomenclature, call_back.from_user.id,
                                                                      call_back.id)
        else:
            current_description = await self.description_nomenclature(call_back.data, call_back.from_user.id,
                                                                      call_back.id)
        arr_answer = await self.send_photo(call_back.message, current_description[0], current_description[1])
        menu_button = self.data.get_description_button(call_back.from_user.id)
        answer_description = await self.answer_message(arr_answer[0], current_description[2],
                                                       self.build_keyboard(menu_button, 2))
        arr_answer.append(answer_description)
        arr_message = []
        for item_message in arr_answer:
            arr_message.append(str(item_message.message_id))
        await self.delete_messages(call_back.from_user.id)
        self.add_arr_messages(call_back.from_user.id, arr_message)

    async def return_description(self, call_back: CallbackQuery, id_nomenclature: str):
        whitespace = '\n'
        arr_description = self.current_description(id_nomenclature)
        description_text = f'{arr_description[4]}{whitespace}' \
                           f'{arr_description[5]}'
        if re.sub('\W+', '', description_text) == "":
            description_text = "Нет подробной информации"
        menu_button = self.data.get_description_button(call_back.from_user.id)
        await self.edit_message(call_back.message, description_text, self.build_keyboard(menu_button, 2))

    async def add_nomenclature(self, call_back: CallbackQuery):
        whitespace = '\n'
        text = f"Введите количество, которое нужно добавить в корзину:{whitespace}"
        menu_button = self.data.get_calculater_keyboard(call_back.from_user.id)
        await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))

    async def add_nomenclature_from_basket(self, call_back: CallbackQuery, id_nomenclature: str):
        whitespace = '\n'
        current_description = await self.description_nomenclature(id_nomenclature, call_back.from_user.id, call_back.id)
        description_text = f"Введите количество, которое нужно добавить в корзину:{whitespace}"
        arr_answer = await self.send_photo(call_back.message, current_description[0], current_description[1])
        menu_button = self.data.get_calculater_keyboard(call_back.from_user.id)
        answer_description = await self.answer_message(arr_answer[0], description_text,
                                                       self.build_keyboard(menu_button, 3))
        arr_answer.append(answer_description)
        arr_message = []
        for item_message in arr_answer:
            arr_message.append(str(item_message.message_id))
        await self.delete_messages(call_back.from_user.id)
        self.add_arr_messages(call_back.from_user.id, arr_message)

    async def change_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.previous_history(call_back.from_user.id)
        arr_description = self.current_description(id_nomenclature)
        if len(call_back.message.text.split(whitespace)) == 2:
            amount = call_back.message.text.split(' шт')[0].split(whitespace)[1] + call_back.data
            if amount[0] == '0':
                amount = call_back.data
        else:
            amount = call_back.data
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = arr_description[9]
        else:
            price = arr_description[8]
        sum_nomenclature = float(amount) * float(price)
        text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
               f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
        menu_button = self.data.get_calculater_keyboard(call_back.from_user.id)
        try:
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
        except TelegramBadRequest as error:
            pass

    async def minus_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.previous_history(call_back.from_user.id)
        arr_description = self.current_description(id_nomenclature)
        if len(call_back.message.text.split(whitespace)) == 2:
            amount = call_back.message.text.split(' шт')[0].split(whitespace)[1]
            if int(amount) == 0:
                amount = 0
            else:
                amount = int(amount) - 1
        else:
            amount = None
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = arr_description[9]
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            menu_button = self.data.get_calculater_keyboard(call_back.from_user.id)
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                pass
        else:
            pass

    async def plus_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.previous_history(call_back.from_user.id)
        arr_description = self.current_description(id_nomenclature)
        if len(call_back.message.text.split(whitespace)) == 2:
            amount = call_back.message.text.split(' шт')[0].split(whitespace)[1]
            if int(amount) == 0:
                amount = 1
            else:
                amount = int(amount) + 1
        else:
            amount = None
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = arr_description[9]
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            menu_button = self.data.get_calculater_keyboard(call_back.from_user.id)
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                pass
        else:
            pass

    async def delete_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.previous_history(call_back.from_user.id)
        arr_description = self.current_description(id_nomenclature)
        if len(call_back.message.text.split(whitespace)) == 2:
            amount = call_back.message.text.split(' шт')[0].split(whitespace)[1]
            if len(amount) > 1:
                amount = amount[:-1]
            else:
                amount = 0
        else:
            amount = None
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = arr_description[9]
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            menu_button = self.data.get_calculater_keyboard(call_back.from_user.id)
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                pass
        else:
            pass

    async def add_to_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.previous_history(call_back.from_user.id)
        arr_description = self.current_description(id_nomenclature)
        if len(call_back.message.text.split(whitespace)) == 2:
            amount = call_back.message.text.split(' шт')[0].split(whitespace)[1]
            if int(amount) == 0:
                amount = None
        else:
            amount = None
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            if arr_description[9] is None or arr_description[9] == '':
                await self.bot.alert_message(call_back.id, 'На данный товар нет дилерской цены!')
                price = 0
            else:
                price = arr_description[9]
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            add_item = f"{id_nomenclature}///{amount}///{sum_nomenclature}"
            basket = self.current_basket(call_back.from_user.id)
            if basket is None:
                self.add_basket_base(call_back.from_user.id, add_item)
            else:
                basket.append(add_item)
                self.add_basket_base(call_back.from_user.id, ' '.join(basket))
            text = f"Вы добавили {arr_description[2]} в количестве " \
                   f"{amount} шт. на сумму {self.format_price(float(sum_nomenclature))} в корзину."
            menu_button = self.data.get_description_button(call_back.from_user.id)
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                pass
        else:
            pass

    async def show_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket = self.current_basket(call_back.from_user.id)
        if current_basket is None:
            text = 'Ваша корзина пуста 😭😔💔'
            menu_button = {'back': '◀ 👈 Назад'}
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 1))
        else:
            sum_item = 0
            for item in current_basket:
                arr_item = item.split('///')
                sum_item += float(arr_item[2])
            text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_item))}:"
            menu_button = {'back_basket': '◀ 👈 Назад', 'post': 'Отправить заказ 📧📦📲'}
            heading = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            await self.delete_messages(call_back.from_user.id, heading.message_id)
            arr_answers = []
            for item in current_basket:
                row = item.split('///')
                name = self.current_description(row[0])[2]
                text = f"{name}:{whitespace}{row[1]} шт. на сумму {self.format_price(float(row[2]))}"
                menu_button = {'basket_minus': '➖', 'basket_plus': '➕'}
                answer = await self.answer_message(heading, text, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            self.add_arr_messages(call_back.from_user.id, arr_answers)

    async def description_nomenclature(self, id_item: str, id_user: int, id_call_back: str):
        whitespace = '\n'
        arr_description = self.current_description(id_item)
        if arr_description[7] == "0":
            availability = "Нет на складе"
        else:
            availability = arr_description[7]
        if self.arr_auth_user[id_user] == 'diler':
            if arr_description[9] is None or arr_description[9] == '':
                await self.bot.alert_message(id_call_back, 'На данный товар нет дилерской цены!')
                dealer = 0
            else:
                dealer = arr_description[9]
            info_nomenclature = f'{self.format_text(arr_description[2])}{whitespace}' \
                                f'Артикул: {self.format_text(arr_description[0])}{whitespace}' \
                                f'Бренд: {self.format_text(arr_description[1])}{whitespace}' \
                                f'Цена: {self.format_text(self.format_price(float(arr_description[8])))}{whitespace}' \
                                f'Дилерская цена: {self.format_text(self.format_price(float(dealer)))}' \
                                f'{whitespace}' \
                                f'Наличие: {self.format_text(availability)}{whitespace}'
        else:
            info_nomenclature = f'{self.format_text(arr_description[2])}{whitespace}' \
                                f'Артикул: {self.format_text(arr_description[0])}{whitespace}' \
                                f'Бренд: {self.format_text(arr_description[1])}{whitespace}' \
                                f'Цена: {self.format_text(self.format_price(float(arr_description[8])))}{whitespace}' \
                                f'Наличие: {self.format_text(availability)}{whitespace}'
        description_text = f'{arr_description[4]}{whitespace}' \
                           f'{arr_description[5]}'
        if re.sub('\W+', '', description_text) == "":
            description_text = "Нет подробной информации"
        return arr_description[6], info_nomenclature, description_text

    async def list_nomenclature(self, call_back: CallbackQuery):
        number_page = '\n' + 'Страница №1'
        current_nomenclature = self.current_nomenclature(call_back.data)
        pages = {}
        for page in current_nomenclature.keys():
            pages[page] = page
        heading = await self.edit_message(call_back.message, self.text_category(call_back.data) + number_page,
                                          self.build_keyboard(pages, 5))
        arr_answers = []
        for key, value in current_nomenclature['Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(call_back.from_user.id, arr_answers)

    def current_basket(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_basket(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_basket(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_basket = f"SELECT BASKET FROM TELEGRAMMBOT WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_basket)
        basket = curs.fetchone()[0]
        if basket is None:
            return None
        else:
            return basket.split()

    def add_basket_base(self, id_user: int, record_item: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                self.execute_add_basket_base(id_user, record_item)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_add_basket_base(self, id_user: int, record_item: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"BASKET = '{record_item}' " \
                     f"WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

    def previous_history(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_previous_history(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_previous_history(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_history = f"SELECT HISTORY FROM TELEGRAMMBOT " \
                      f"WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_history)
        row_table = curs.fetchone()[0]
        return row_table.split()[-2]

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

    def current_description(self, kod_nomenclature: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_description(kod_nomenclature)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_description(self, kod_nomenclature: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_nomenclature = f"SELECT ARTICLE, BRAND, NAME, DISCOUNT, DESCRIPTION, SPECIFICATION, PHOTO, AVAILABILITY, " \
                           f"PRICE, DEALER, DISTRIBUTOR " \
                           f"FROM NOMENCLATURE " \
                           f"WHERE KOD = '{kod_nomenclature}' "
        curs.execute(sql_nomenclature)
        row_table = curs.fetchone()
        return row_table

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
        sql_auth = f"SELECT ID_USER FROM TELEGRAMMBOT " \
                   f"WHERE ID_USER = {self.quote(message.from_user.id)} "
        curs.execute(sql_auth)
        row_table = curs.fetchone()
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
        sql_record = f"INSERT INTO TELEGRAMMBOT (ID_USER, HISTORY, MESSAGES, EMAIL) " \
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
        sql_auth = f"SELECT ID_USER, STATUS FROM TELEGRAMMBOT "
        curs.execute(sql_auth)
        dict_user = {}
        for item in curs.fetchall():
            dict_user[int(item[0])] = item[1]
        return dict_user

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
        sql_number_chat = f"SELECT MESSAGES FROM TELEGRAMMBOT " \
                          f"WHERE ID_USER = {self.quote(user_id)} "
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
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"MESSAGES = '{record_message}' " \
                     f"WHERE ID_USER = {self.quote(user_id)} "
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
        sql_auth = f"SELECT HISTORY, MESSAGES, EMAIL FROM TELEGRAMMBOT " \
                   f"WHERE ID_USER = {self.quote(id_user)} "
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
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"HISTORY = '{history}' " \
                     f"WHERE ID_USER = {self.quote(id_user)} "
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
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"HISTORY = '{history}' " \
                     f"WHERE ID_USER = {self.quote(id_user)} "
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
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"MESSAGES = '{arr_messages}' " \
                     f"WHERE ID_USER = {self.quote(id_user)} "
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
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"MESSAGES = '{arr_messages}' " \
                     f"WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

    def build_keyboard(self, dict_button: dict, column: int, dict_return_button=None):
        keyboard = self.build_menu(self.get_list_keyboard_button(dict_button), column,
                                   footer_buttons=self.get_list_keyboard_button(dict_return_button))
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
        cleaner = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        clean_text = re.sub(cleaner, '', text_message)
        return f'<b>{clean_text}</b>'

    @staticmethod
    def format_price(item: float):
        return '{0:,} ₽'.format(item).replace(',', ' ')

    @staticmethod
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
        self.calculater = {'1': '1⃣', '2': '2⃣', '3': '3⃣', '4': '4⃣', '5': '5⃣', '6': '6⃣', '7': '7⃣', '8': '8️⃣',
                           '9': '9⃣', 'back': '◀👈 Назад', '0': '0️⃣', 'done': 'Готово ✅🗑️',
                           'minus': '➖', 'delete': '⌫', 'plus': '➕',
                           'basket': f'Корзина 🛒(0 шт на 0 руб.)'}
        self.description_button = {'back': '◀ 👈 Назад', 'add': 'Добавить ✅🗑️',
                                   'basket': f'Корзина 🛒(0 шт на 0 руб.)'}

    @property
    def get_first_keyboard(self):
        return self.first_keyboard

    @property
    def get_prices(self):
        return self.price

    @property
    def get_category(self):
        dict_category = {}
        for item in range(400, 2000):
            dict_category[str(item)] = str(item)
        return dict_category

    @property
    def get_pages(self):
        dict_pages = {}
        for item in range(100):
            dict_pages['Стр.' + str(item)] = str(item)
        return dict_pages

    @property
    def get_nomenclature(self):
        dict_nomenclature = {}
        for item in range(4000, 30000):
            dict_nomenclature[str(item)] = str(item)
        return dict_nomenclature

    @property
    def get_button_calculater(self):
        dict_button_calculater = {}
        for item in range(10):
            dict_button_calculater[str(item)] = str(item)
        return dict_button_calculater

    def current_basket(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_basket(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_basket(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_basket = f"SELECT BASKET FROM TELEGRAMMBOT WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_basket)
        basket = curs.fetchone()[0]
        if basket is None:
            return None
        else:
            return basket.split()

    def get_calculater_keyboard(self, id_user: int):
        arr_basket = self.current_basket(id_user)
        if arr_basket is None:
            self.calculater['basket'] = f"Корзина 🛒(0 шт. на 0 ₽)"
        else:
            sum_item = 0
            for item in arr_basket:
                arr_item = item.split('///')
                sum_item += float(arr_item[2])
            self.calculater['basket'] = f"Корзина 🛒({len(arr_basket)} шт. на {self.format_price(float(sum_item))})"
        return self.calculater

    def get_description_button(self, id_user: int):
        arr_basket = self.current_basket(id_user)
        if arr_basket is None:
            self.description_button['basket'] = f"Корзина 🛒(0 шт. на 0 ₽)"
        else:
            sum_item = 0
            for item in arr_basket:
                arr_item = item.split('///')
                sum_item += float(arr_item[2])
            self.description_button['basket'] = f"Корзина 🛒({len(arr_basket)} шт. " \
                                                f"на {self.format_price(float(sum_item))})"
        return self.description_button

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"

    @staticmethod
    def format_price(item: float):
        return '{0:,} ₽'.format(item).replace(',', ' ')
