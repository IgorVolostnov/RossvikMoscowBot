import asyncio
import logging
import requests
import json
import re
import os
import sqlite3
from asyncio import Queue
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, FSInputFile
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

    async def edit_head_message(self, text_message: str, chat_message: int, id_message: int,
                                keyboard: InlineKeyboardMarkup):
        await self.edit_message_text(text=self.format_text(text_message), chat_id=chat_message, message_id=id_message,
                                     parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def push_photo(self, message_chat_id: int, text: str, keyboard: InlineKeyboardMarkup):
        photo_to_read = os.path.join(os.path.dirname(__file__), 'Catalog.png')
        return await self.send_photo(chat_id=message_chat_id, photo=FSInputFile(photo_to_read), caption=text,
                                     parse_mode=ParseMode.HTML, reply_markup=keyboard)

    @staticmethod
    def format_text(text_message: str):
        cleaner = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        clean_text = re.sub(cleaner, '', text_message)
        return f'<b>{clean_text}</b>'


class DispatcherMessage(Dispatcher):
    def __init__(self, parent, **kw):
        Dispatcher.__init__(self, **kw)
        self.timer = TimerClean(self, 300)
        self.bot = parent
        self.arr_auth_user = self.auth_user
        self.data = DATA()
        self.first_keyboard = self.data.get_first_keyboard
        self.category = self.data.get_category
        self.pages = self.data.get_pages
        self.pages_search = self.data.get_pages_search
        self.nomenclatures = self.data.get_nomenclature
        self.button_calculater = self.data.get_button_calculater
        self.button_basket_minus = self.data.get_basket_minus
        self.button_basket_plus = self.data.get_basket_plus
        self.levels_in_keyboard = self.data.get_levels_category
        self.level_numbers = self.data.get_level_numbers
        self.queue = Queue

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            answer = await self.answer_message(message, "Выберете, что Вас интересует",
                                               self.build_keyboard(self.first_keyboard, 2))
            if self.start_message(message):
                self.restart_record(message)
                self.add_element_message(message.from_user.id, message.message_id)
            else:
                self.start_record_new_user(message)
            await self.delete_messages(message.from_user.id)
            self.add_element_message(message.from_user.id, answer.message_id)
            await self.timer.start(message.from_user.id)

        @self.message(Command("catalog"))
        async def cmd_catalog(message: Message):
            if self.arr_auth_user[message.from_user.id] == 'creator':
                menu_button = {'back': '◀ 👈 Назад'}
                answer = await self.bot.push_photo(message.chat.id, self.format_text("Каталог товаров ROSSVIK 📖"),
                                                   self.build_keyboard(self.data.get_price_creator, 2, menu_button))
            else:
                menu_button = {'back': '◀ 👈 Назад'}
                answer = await self.bot.push_photo(message.chat.id, self.format_text("Каталог товаров ROSSVIK 📖"),
                                                   self.build_keyboard(self.data.get_prices, 1, menu_button))
            self.add_element_message(message.from_user.id, message.message_id)
            await self.delete_messages(message.from_user.id)
            self.add_element_message(message.from_user.id, answer.message_id)
            self.restart_catalog(message)
            await self.timer.start(message.from_user.id)

        @self.message(F.from_user.id.in_(self.arr_auth_user) & F.content_type.in_({
            "text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact",
            "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
            "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
            "migrate_from_chat_id", "pinned_message"}))
        async def send_message_search(message: Message):
            id_user = message.from_user.id
            result_search = self.search(message.text)
            current_history = self.current_history(id_user)
            if len(result_search['Поиск_Стр.1']) == 0:
                await self.find_nothing(id_user, message)
                if 'search' in current_history:
                    await self.timer.start(id_user)
                elif 'Поиск' in current_history:
                    self.delete_element_history(id_user)
                    await self.timer.start(id_user)
                else:
                    self.add_element_history(id_user, f'search___{self.change_record_search(message.text)}')
                    await self.timer.start(id_user)
            else:
                await self.show_result_search(id_user, message, result_search)
                if 'search' in current_history:
                    self.delete_element_history(id_user)
                    self.add_element_history(id_user, f"search___{self.change_record_search(message.text)} Поиск_Стр.1")
                    await self.timer.start(id_user)
                elif 'Поиск' in current_history:
                    self.delete_element_history(id_user)
                    self.delete_element_history(id_user)
                    self.add_element_history(id_user, f"search___{self.change_record_search(message.text)} Поиск_Стр.1")
                    await self.timer.start(id_user)
                else:
                    self.add_element_history(id_user, f"search___{self.change_record_search(message.text)} Поиск_Стр.1")
                    await self.timer.start(id_user)

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
                self.add_element_history(callback.from_user.id, f"{callback.data} Стр.1")
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages)))
        async def send_next_page(callback: CallbackQuery):
            if await self.next_page(callback):
                self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages_search)))
        async def send_next_page_search(callback: CallbackQuery):
            previous_history = self.delete_element_history(callback.from_user.id)
            result_search = self.search(self.get_text_for_search(previous_history.split('___')[1]))
            if await self.next_page_search(callback, result_search):
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
            if await self.add_to_basket(callback):
                self.delete_element_history(callback.from_user.id)
                await self.timer.start(callback.from_user.id)
            else:
                await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'basket'))
        async def send_show_basket(callback: CallbackQuery):
            await self.show_basket(callback)
            self.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.button_basket_minus)))
        async def send_basket_minus(callback: CallbackQuery):
            await self.minus_amount_basket(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.button_basket_plus)))
        async def send_basket_plus(callback: CallbackQuery):
            await self.plus_amount_basket(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'clean'))
        async def send_clean_basket(callback: CallbackQuery):
            self.clean_basket(callback.from_user.id)
            current = self.delete_element_history(callback.from_user.id)
            if current in self.nomenclatures:
                await self.description(callback, current)
                await self.timer.start(callback.from_user.id)
            elif current == 'add':
                previous_history = self.previous_history(callback.from_user.id)
                await self.add_nomenclature_from_basket(callback, previous_history)
                await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'back'))
        async def send_return_message(callback: CallbackQuery):
            current = self.delete_element_history(callback.from_user.id)
            if 'search' in current:
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
            elif current in self.pages_search:
                previous_history = self.delete_element_history(callback.from_user.id)
                result_search = self.search(self.get_text_for_search(previous_history.split('___')[1]))
                await self.return_page_search(callback, result_search, current)
                self.add_element_history(callback.from_user.id, current)
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

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.levels_in_keyboard)))
        async def send_change_level(callback: CallbackQuery):
            current_history = self.current_history(callback.from_user.id)
            if current_history == 'catalog':
                await self.show_level_price(callback)
                self.add_element_history(callback.from_user.id, 'level')
            elif current_history in self.category:
                await self.show_level_category(callback, current_history)
                self.add_element_history(callback.from_user.id, 'level')
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.level_numbers)))
        async def send_new_level(callback: CallbackQuery):
            current_history = self.delete_element_history(callback.from_user.id)
            if current_history == 'catalog':
                kod_nomenclature = callback.message.caption.split('Код:')[1]
                kod_install = self.level_numbers[callback.data]
                self.data.set_price_level(kod_nomenclature, int(kod_install))
                await self.catalog(callback)
            elif current_history in self.category:
                kod_parent = current_history
                kod_category = callback.message.caption.split('Код:')[1]
                level_install = self.level_numbers[callback.data]
                self.set_category_level(kod_parent, kod_category, int(level_install))
                await self.return_category(callback, current_history)
            await self.timer.start(callback.from_user.id)

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_caption(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_caption(caption=self.format_text(text), parse_mode=ParseMode.HTML,
                                          reply_markup=keyboard)

    @staticmethod
    async def edit_keyboard(message: Message, keyboard: InlineKeyboardMarkup):
        return await message.edit_reply_markup(reply_markup=keyboard)

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

    @staticmethod
    async def checkout_admin(queue: Queue, admin_number: int):
        while not queue.empty():
            user: USER = await queue.get()
            print(f"The Admin_{admin_number} "
                  f"will checkout User_{user.id_user}")
            # for product in customer.products:
            #     print(f"The Cashier_{cashier_number} "
            #           f"will checkout Customer_{customer.customer_id}'s "
            #           f"Product_{product.product_name}")
            #     await asyncio.sleep(product.checkout_time)
            # print(f"The Cashier_{cashier_number} "
            #       f"finished checkout Customer_{customer.customer_id}")
            queue.task_done()

    async def find_nothing(self, id_user: int, message: Message):
        self.add_element_message(id_user, message.message_id)
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.answer_message(message, "Сожалеем, но ничего не найдено.",
                                           self.build_keyboard(menu_button, 1))
        await self.delete_messages(id_user)
        self.add_element_message(id_user, answer.message_id)

    async def show_result_search(self, id_user: int, message: Message, result_search: dict):
        self.add_element_message(id_user, message.message_id)
        number_page = '\n' + 'Страница №1'
        pages = {}
        for page in result_search.keys():
            pages[page] = page
        heading = await self.answer_message(message, self.format_text(f"Результаты поиска:{number_page}"),
                                            self.build_keyboard(pages, 5))
        await self.delete_messages(id_user)
        arr_answers = [str(heading.message_id)]
        for key, value in result_search['Поиск_Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(id_user, arr_answers)

    async def next_page_search(self, call_back: CallbackQuery, result_search: dict):
        if self.pages_search[call_back.data] == call_back.message.text.split('№')[1]:
            return False
        else:
            pages = {}
            for page in result_search.keys():
                pages[page] = page
            heading = await self.edit_message(call_back.message,
                                              f"{call_back.message.text.split('№')[0]}"
                                              f"№{self.pages_search[call_back.data]}",
                                              self.build_keyboard(pages, 5))
            await self.delete_messages(call_back.from_user.id, heading.message_id)
            arr_answers = []
            for key, value in result_search[call_back.data].items():
                menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
                answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            self.add_arr_messages(call_back.from_user.id, arr_answers)
            return True

    async def return_page_search(self, call_back: CallbackQuery, result_search: dict, current_page: str):
        number_page = '\n' + 'Страница №' + self.pages_search[current_page]
        pages = {}
        for page in result_search.keys():
            pages[page] = page
        heading = await self.edit_message(call_back.message,
                                          self.format_text(f"Результаты поиска:{number_page}"),
                                          self.build_keyboard(pages, 5))
        await self.delete_messages(call_back.from_user.id, heading.message_id)
        await asyncio.sleep(0.5)
        arr_answers = []
        for key, value in result_search[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(call_back.from_user.id, arr_answers)

    async def return_start(self, call_back: CallbackQuery):
        answer = await self.answer_message(call_back.message, "Выберете, что Вас интересует",
                                           self.build_keyboard(self.first_keyboard, 2))
        await self.delete_messages(call_back.from_user.id)
        self.add_element_message(call_back.from_user.id, answer.message_id)

    async def catalog(self, call_back: CallbackQuery):
        if self.arr_auth_user[call_back.from_user.id] == 'creator':
            menu_button = {'back': '◀ 👈 Назад'}
            answer = await self.bot.push_photo(call_back.message.chat.id, self.format_text("Каталог товаров ROSSVIK 📖"),
                                               self.build_keyboard(self.data.get_price_creator, 2, menu_button))
        else:
            menu_button = {'back': '◀ 👈 Назад'}
            answer = await self.bot.push_photo(call_back.message.chat.id, self.format_text("Каталог товаров ROSSVIK 📖"),
                                               self.build_keyboard(self.data.get_prices, 1, menu_button))
        await self.delete_messages(call_back.from_user.id)
        self.add_element_message(call_back.from_user.id, answer.message_id)

    async def next_category(self, call_back: CallbackQuery):
        current_category = self.current_category(call_back.data)
        if current_category:
            await self.create_keyboard_edit_caption(call_back, current_category, call_back.data)
            return True
        else:
            await self.list_nomenclature(call_back)
            return False

    async def return_category(self, call_back: CallbackQuery, current_history):
        current_category = self.current_category(current_history)
        if current_category:
            await self.create_keyboard_edit_caption(call_back, current_category, current_history)
        else:
            new_current = self.delete_element_history(call_back.from_user.id)
            if new_current == 'catalog':
                if call_back.message.caption:
                    answer_message = await self.create_price_edit_caption(call_back)
                    await self.delete_messages(call_back.from_user.id, answer_message.message_id)
                else:
                    await self.catalog(call_back)
            else:
                current_category = self.current_category(new_current)
                await self.create_keyboard_push_photo(call_back, current_category, new_current)

    async def create_price_edit_caption(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        if self.arr_auth_user[call_back.from_user.id] == 'creator':
            answer = await self.edit_caption(call_back.message,
                                             self.format_text("Каталог товаров ROSSVIK 📖"),
                                             self.build_keyboard(self.data.get_price_creator, 2, menu_button))
        else:
            answer = await self.edit_caption(call_back.message,
                                             self.format_text("Каталог товаров ROSSVIK 📖"),
                                             self.build_keyboard(self.data.get_prices, 1, menu_button))
        return answer

    async def create_keyboard_edit_caption(self, call_back: CallbackQuery, list_category: list, id_category: str):
        menu_button = {'back': '◀ 👈 Назад'}
        if self.arr_auth_user[call_back.from_user.id] == 'creator':
            await self.edit_caption(call_back.message,
                                    self.text_category(id_category),
                                    self.build_keyboard(self.data.get_category_creator(list_category),
                                                        2, menu_button))
        else:
            await self.edit_caption(call_back.message,
                                    self.text_category(id_category),
                                    self.build_keyboard(self.assembling_category_dict(list_category),
                                                        1, menu_button))

    async def create_keyboard_push_photo(self, call_back: CallbackQuery, list_category: list, id_category: str):
        menu_button = {'back': '◀ 👈 Назад'}
        if self.arr_auth_user[call_back.from_user.id] == 'creator':
            answer = await self.bot.push_photo(call_back.message.chat.id,
                                               self.format_text(self.text_category(id_category)),
                                               self.build_keyboard(self.data.get_category_creator(list_category),
                                                                   2, menu_button))
            await self.delete_messages(call_back.from_user.id)
            self.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.bot.push_photo(call_back.message.chat.id,
                                               self.format_text(self.text_category(id_category)),
                                               self.build_keyboard(self.assembling_category_dict(list_category),
                                                                   1, menu_button))
            await self.delete_messages(call_back.from_user.id)
            self.add_element_message(call_back.from_user.id, answer.message_id)

    async def next_page(self, call_back: CallbackQuery):
        if self.pages[call_back.data] == call_back.message.caption.split('№')[1]:
            return False
        else:
            id_category = self.delete_element_history(call_back.from_user.id)
            current_nomenclature = self.current_nomenclature(id_category)
            pages = {}
            for page in current_nomenclature.keys():
                pages[page] = page
            heading = await self.edit_caption(call_back.message,
                                              f"{call_back.message.caption.split('№')[0]}"
                                              f"№{self.pages[call_back.data]}",
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
        heading = await self.bot.push_photo(call_back.message.chat.id, self.format_text(text + number_page),
                                            self.build_keyboard(pages, 5))
        await self.delete_messages(call_back.from_user.id)
        await asyncio.sleep(0.5)
        arr_answers = [str(heading.message_id)]
        for key, value in current_nomenclature[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(call_back.from_user.id, arr_answers)

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
            if arr_description[9] is None or arr_description[9] == '' or arr_description[9] == '0':
                price = arr_description[8]
            else:
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
            if arr_description[9] is None or arr_description[9] == '' or arr_description[9] == '0':
                price = arr_description[8]
            else:
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
            if arr_description[9] is None or arr_description[9] == '' or arr_description[9] == '0':
                price = arr_description[8]
            else:
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
        if arr_description[9] is None or arr_description[9] == '' or arr_description[9] == '0':
            if arr_description[9] is None or arr_description[9] == '':
                price = arr_description[8]
            else:
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
        amount = await self.check_amount(call_back.message.text, call_back.id, arr_description[7])
        price = self.check_price(call_back.from_user.id, arr_description[9], arr_description[8])
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            basket = self.current_basket_dict(call_back.from_user.id)
            basket[id_nomenclature] = [amount, sum_nomenclature]
            self.add_basket_base(call_back.from_user.id, self.assembling_basket_dict(basket))
            text = f"Вы добавили {arr_description[2]} в количестве:{whitespace}" \
                   f"{amount} шт. на сумму {self.format_price(float(sum_nomenclature))} в корзину."
            menu_button = self.data.get_description_button(call_back.from_user.id)
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
                return True
            except TelegramBadRequest as error:
                pass
        else:
            return False

    async def check_amount(self, text_message: str, id_call_back: str, amount_in_base: str):
        whitespace = '\n'
        if amount_in_base == 'Нет на складе':
            amount_in_base = '0'
        if len(text_message.split(whitespace)) == 2:
            amount = text_message.split(' шт')[0].split(whitespace)[1]
            if int(amount) == 0:
                await self.bot.alert_message(id_call_back, 'Вы хотите добавить 0 товара в корзину!')
                amount = None
            elif int(amount) > int(amount_in_base):
                await self.bot.alert_message(id_call_back, 'Нельзя добавить товара больше, чем есть на остатках!')
                amount = None
        else:
            await self.bot.alert_message(id_call_back, 'Выберете количество товара, которое нужно добавить в корзину!')
            amount = None
        return amount

    def check_price(self, id_user: int, dealer_price: str, retail_price: str):
        if self.arr_auth_user[id_user] == 'diler':
            if dealer_price is None or dealer_price == '' or dealer_price == '0':
                price = retail_price
            else:
                price = dealer_price
        else:
            price = retail_price
        return price

    async def show_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket_dict = self.current_basket_dict(call_back.from_user.id)
        if len(current_basket_dict) == 0:
            text = 'Ваша корзина пуста 😭😔💔'
            menu_button = {'back': '◀ 👈 Назад'}
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 1))
        else:
            sum_basket = self.sum_basket(current_basket_dict)
            text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            menu_button = {'back_basket': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                           'post': 'Отправить заказ 📧📦📲'}
            heading = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            await self.delete_messages(call_back.from_user.id, heading.message_id)
            arr_answers = []
            for key, item in current_basket_dict.items():
                name = self.current_description(key)[2]
                text = f"{name}:{whitespace}{item[0]} шт. на сумму {self.format_price(float(item[1]))}"
                menu_button = {f'basket_minus{key}': '➖', f'basket_plus{key}': '➕'}
                answer = await self.answer_message(heading, text, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            self.add_arr_messages(call_back.from_user.id, arr_answers)

    async def minus_amount_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket_dict = self.current_basket_dict(call_back.from_user.id)
        current_amount = float(current_basket_dict[self.button_basket_minus[call_back.data]][0])
        price = float(current_basket_dict[self.button_basket_minus[call_back.data]][1]) / float(current_amount)
        if current_amount > 1:
            current_amount -= 1
            current_basket_dict[self.button_basket_minus[call_back.data]] = [str(current_amount),
                                                                             str(price * current_amount)]
            self.add_basket_base(call_back.from_user.id, self.assembling_basket_dict(current_basket_dict))
            name = self.current_description(self.button_basket_minus[call_back.data])[2]
            text = f"{name}:{whitespace}{int(current_amount)} шт. на сумму {self.format_price(price * current_amount)}"
            menu_button = {f'basket_minus{self.button_basket_minus[call_back.data]}': '➖',
                           f'basket_plus{self.button_basket_minus[call_back.data]}': '➕'}
            sum_basket = self.sum_basket(current_basket_dict)
            head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            head_menu_button = {'back_basket': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                'post': 'Отправить заказ 📧📦📲'}
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            await self.bot.edit_head_message(head_text, call_back.message.chat.id,
                                             self.get_arr_messages(call_back.from_user.id)[0],
                                             self.build_keyboard(head_menu_button, 2))
        else:
            current_basket_dict.pop(self.button_basket_minus[call_back.data])
            if len(current_basket_dict) == 0:
                self.clean_basket(call_back.from_user.id)
                await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
                head_text = 'Ваша корзина пуста 😭😔💔'
                head_menu_button = {'back_basket': '◀ 👈 Назад'}
                await self.bot.edit_head_message(head_text, call_back.message.chat.id,
                                                 self.get_arr_messages(call_back.from_user.id)[0],
                                                 self.build_keyboard(head_menu_button, 1))
            else:
                self.add_basket_base(call_back.from_user.id, self.assembling_basket_dict(current_basket_dict))
                await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
                sum_basket = self.sum_basket(current_basket_dict)
                head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                            f"{self.format_price(float(sum_basket))}:"
                head_menu_button = {'back_basket': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                    'post': 'Отправить заказ 📧📦📲'}
                await self.bot.edit_head_message(head_text, call_back.message.chat.id,
                                                 self.get_arr_messages(call_back.from_user.id)[0],
                                                 self.build_keyboard(head_menu_button, 2))

    async def plus_amount_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket_dict = self.current_basket_dict(call_back.from_user.id)
        current_amount = float(current_basket_dict[self.button_basket_plus[call_back.data]][0])
        price = float(current_basket_dict[self.button_basket_plus[call_back.data]][1]) / float(current_amount)
        availability = self.current_description(self.button_basket_plus[call_back.data])[7]
        if str(int(current_amount)) == availability or availability == "Нет на складе":
            await self.bot.alert_message(call_back.id, 'Нельзя добавить товара больше, чем есть на остатках!')
        else:
            current_amount += 1
            current_basket_dict[self.button_basket_plus[call_back.data]] = [str(current_amount),
                                                                            str(price * current_amount)]
            self.add_basket_base(call_back.from_user.id, self.assembling_basket_dict(current_basket_dict))
            name = self.current_description(self.button_basket_plus[call_back.data])[2]
            text = f"{name}:{whitespace}{int(current_amount)} шт. на сумму {self.format_price(price * current_amount)}"
            menu_button = {f'basket_minus{self.button_basket_plus[call_back.data]}': '➖',
                           f'basket_plus{self.button_basket_plus[call_back.data]}': '➕'}
            sum_basket = self.sum_basket(current_basket_dict)
            head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            head_menu_button = {'back_basket': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                'post': 'Отправить заказ 📧📦📲'}
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            await self.bot.edit_head_message(head_text, call_back.message.chat.id,
                                             self.get_arr_messages(call_back.from_user.id)[0],
                                             self.build_keyboard(head_menu_button, 2))

    async def description_nomenclature(self, id_item: str, id_user: int, id_call_back: str):
        whitespace = '\n'
        arr_description = self.current_description(id_item)
        if arr_description[7] == "0":
            availability = "Нет на складе"
        else:
            availability = arr_description[7]
        if self.arr_auth_user[id_user] == 'diler':
            if arr_description[9] is None or arr_description[9] == '' or arr_description[9] == '0':
                await self.bot.alert_message(id_call_back, 'На данный товар нет дилерской цены!')
                dealer = arr_description[8]
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
        heading = await self.edit_caption(call_back.message,
                                          self.format_text(self.text_category(call_back.data) + number_page),
                                          self.build_keyboard(pages, 5))
        arr_answers = []
        for key, value in current_nomenclature['Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        self.add_arr_messages(call_back.from_user.id, arr_answers)

    async def show_level_price(self, call_back: CallbackQuery):
        whitespace = '\n'
        menu_button = {'back': '◀ 👈 Назад'}
        amount_price = len(self.data.price)
        level_keyboard = self.data.level_numbers(amount_price)
        kod = f"Код:{call_back.data.split('level')[1]}"
        name_category = f"{self.text_category(call_back.data.split('level')[1])}{whitespace}" \
                        f"{self.data.get_price_creator[call_back.data]}{whitespace}" \
                        f"{kod}"
        await self.edit_caption(call_back.message, name_category, self.build_keyboard(level_keyboard, 5,
                                                                                      menu_button))

    async def show_level_category(self, call_back: CallbackQuery, id_category: str):
        whitespace = '\n'
        menu_button = {'back': '◀ 👈 Назад'}
        list_category = self.current_category(id_category)
        amount_price = len(list_category)
        level_keyboard = self.data.level_numbers(amount_price)
        kod = f"Код:{call_back.data.split('level')[1]}"
        name_category = f"{self.text_category(call_back.data.split('level')[1])}{whitespace}" \
                        f"{self.data.get_category_creator(list_category)[call_back.data]}{whitespace}" \
                        f"{kod}"
        await self.edit_caption(call_back.message, name_category, self.build_keyboard(level_keyboard, 5,
                                                                                      menu_button))

    def set_category_level(self, kod_parent: str, kod_category: str, level: int):
        end_number = 1
        list_category = sorted(self.current_category(kod_parent), key=itemgetter(2), reverse=False)
        for item in list_category:
            if item[0] == kod_category:
                self.set_level(kod_category, level)
            else:
                if end_number == level:
                    end_number += 1
                    self.set_level(item[0], end_number)
                    end_number += 1
                else:
                    self.set_level(item[0], end_number)
                    end_number += 1

    def get_category_by_level(self, level: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_get_category_by_level(level)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_get_category_by_level(self, level: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_category_by_level = f"SELECT KOD FROM CATEGORY " \
                                f"WHERE SORT_CATEGORY = '{level}' "
        curs.execute(sql_category_by_level)
        basket = curs.fetchall()
        return basket

    def set_level(self, kod_nomenclature: str, current_level: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_set_level(kod_nomenclature, current_level)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_set_level(self, kod_nomenclature: str, current_level: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE CATEGORY SET " \
                     f"SORT_CATEGORY = '{current_level}' " \
                     f"WHERE KOD = '{kod_nomenclature}' "
        curs.execute(sql_record)
        self.conn.commit()

    def search_in_base_article(self, search_text: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_search_in_base_article(search_text)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_search_in_base_article(self, search_text: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_nomenclature = f"SELECT KOD, NAME, SORT_NOMENCLATURE FROM NOMENCLATURE " \
                           f"WHERE ARTICLE_CHANGE LIKE '%{search_text}%' "
        curs.execute(sql_nomenclature)
        row_table = curs.fetchall()
        return set(row_table)

    def search_in_base_name(self, search_text: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_search_in_base_name(search_text)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_search_in_base_name(self, search_text: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_nomenclature = f"SELECT KOD, NAME, SORT_NOMENCLATURE FROM NOMENCLATURE " \
                           f"WHERE NAME LIKE '%{search_text}%' "
        curs.execute(sql_nomenclature)
        row_table = curs.fetchall()
        return set(row_table)

    def current_basket_dict(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_basket_dict(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_basket_dict(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_basket = f"SELECT BASKET FROM TELEGRAMMBOT WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_basket)
        basket = curs.fetchone()[0]
        basket_dict = {}
        if basket is None:
            basket_dict = {}
        else:
            for item in basket.split():
                row = item.split('///')
                basket_dict[row[0]] = [row[1], row[2]]
        return basket_dict

    def clean_basket(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_clean_basket(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_clean_basket(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"BASKET = NULL " \
                     f"WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_record)
        self.conn.commit()

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

    def current_history(self, id_user: int):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_current_history(id_user)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_current_history(self, id_user: int):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_history = f"SELECT HISTORY FROM TELEGRAMMBOT " \
                      f"WHERE ID_USER = {self.quote(id_user)} "
        curs.execute(sql_history)
        row_table = curs.fetchone()[0]
        return row_table.split()[-1]

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
        sql_category = f"SELECT KOD, NAME_CATEGORY, SORT_CATEGORY FROM CATEGORY " \
                       f"WHERE PARENT_ID = '{id_parent}' "
        curs.execute(sql_category)
        row_table = curs.fetchall()
        return row_table

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
        sql_nomenclature = f"SELECT KOD, NAME, SORT_NOMENCLATURE FROM NOMENCLATURE " \
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

    def restart_catalog(self, message: Message):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                return self.execute_restart_catalog(message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_restart_catalog(self, message: Message):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
        sql_record = f"UPDATE TELEGRAMMBOT SET " \
                     f"HISTORY = '/start catalog' " \
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

    async def delete_messages(self, user_id: int, except_id_message: int = None, individual: bool = False):
        if individual:
            arr_messages = self.get_arr_messages(user_id, except_id_message)
            await self.bot.delete_messages_chat(user_id, [except_id_message])
            self.record_messages_in_base(user_id, ' '.join(arr_messages))
        else:
            if except_id_message:
                arr_messages = self.get_arr_messages(user_id, except_id_message)
                await self.bot.delete_messages_chat(user_id, arr_messages)
                self.record_messages_in_base(user_id, str(except_id_message))
            else:
                arr_messages = self.get_arr_messages(user_id, except_id_message)
                await self.bot.delete_messages_chat(user_id, arr_messages)
                self.record_messages_in_base(user_id, '')

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

    def record_messages_in_base(self, user_id: int, record_message: str):
        try:
            with sqlite3.connect(os.path.join(os.path.dirname(__file__), os.getenv('CONNECTION'))) as self.conn:
                self.execute_record_messages_in_base(user_id, record_message)
        except sqlite3.Error as error:
            print("Ошибка чтения данных из таблицы", error)
        finally:
            if self.conn:
                self.conn.close()

    def execute_record_messages_in_base(self, user_id: int, record_message: str):
        curs = self.conn.cursor()
        curs.execute('PRAGMA journal_mode=wal')
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

    def search(self, text: str):
        total_search = set()
        i = 1
        for item in self.change_for_search_name(text):
            if i == 1:
                search_variant = self.search_in_base_article(self.translit_rus(re.sub('\W+', '', item[0]).upper()))
                for variant in item:
                    search_result_by_name = self.search_in_base_name(variant)
                    search_variant.update(search_result_by_name)
                total_search = search_variant
                i += 1
            else:
                search_variant = self.search_in_base_article(self.translit_rus(re.sub('\W+', '', item[0]).upper()))
                for variant in item:
                    search_result_by_name = self.search_in_base_name(variant)
                    search_variant.update(search_result_by_name)
                total_search = total_search.intersection(search_variant)
                i += 1
        return self.assembling_search(list(total_search))

    @staticmethod
    def change_record_search(text: str):
        list_record = text.split()
        return '/////'.join(list_record)

    @staticmethod
    def get_text_for_search(text: str):
        list_search = text.split('/////')
        return ' '.join(list_search)

    @staticmethod
    def translit_rus(text_cross: str):
        text_list = list(text_cross)
        dict_letters = {'А': 'A', 'а': 'a', 'В': 'B', 'Е': 'E', 'е': 'e', 'К': 'K', 'к': 'k', 'М': 'M', 'Н': 'H',
                        'О': 'O', 'о': 'o', 'Р': 'P', 'р': 'p', 'С': 'C', 'с': 'c', 'Т': 'T', 'Х': 'X', 'х': 'x'}
        for i in range(len(text_list)):
            if text_list[i] in dict_letters.keys():
                text_list[i] = dict_letters[text_list[i]]
        return ''.join(text_list)

    @staticmethod
    def change_for_search_name(text_cross: str):
        text_list = text_cross.split()
        new_text_list = []
        for item in text_list:
            if re.sub('\W+', '', item) != '':
                new_text_list.append([item, item.lower(), item.title()])
        return new_text_list

    @staticmethod
    def assembling_category_dict(list_category: list):
        dict_category = {}
        for item in sorted(list_category, key=itemgetter(2), reverse=False):
            dict_category[item[0]] = item[1]
        return dict_category

    @staticmethod
    def sum_basket(current_basket: dict):
        sum_item = 0
        for item in current_basket.values():
            sum_item += float(item[1])
        return sum_item

    @staticmethod
    def assembling_basket_dict(basket_dict: dict):
        list_basket = []
        for key, value in basket_dict.items():
            item = f'{key}///{value[0]}///{value[1]}'
            list_basket.append(item)
        return ' '.join(list_basket)

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
        for item_nomenclature in sorted(arr, key=itemgetter(2), reverse=False):
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
    def assembling_search(arr: list):
        assembling_dict_search = {}
        dict_m = {}
        i = 1
        y = 1
        for item_nomenclature in sorted(arr, key=itemgetter(2), reverse=False):
            if i < 7:
                dict_m[item_nomenclature[0]] = item_nomenclature[1]
                i += 1

            else:
                assembling_dict_search['Поиск_Стр.' + str(y)] = dict_m
                i = 1
                dict_m = {}
                y += 1
                dict_m[item_nomenclature[0]] = item_nomenclature[1]
                i += 1
        assembling_dict_search['Поиск_Стр.' + str(y)] = dict_m
        return assembling_dict_search

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
        self.price = [['506', 'Шиноремонтные материалы ✂⚒', 100],
                      ['507', 'Вентили 🔌', 100],
                      ['556', 'Ремонтные шипы ‍🌵', 100],
                      ['658', 'Грузики балансировочные ⚖', 100],
                      ['552', 'Шиномонтажное оборудование 🚗🔧', 100],
                      ['600', 'Подъемное оборудование ⛓', 100],
                      ['547', 'Инструмент 🔧', 100],
                      ['608', 'Специнструмент 🛠', 100],
                      ['726', 'Заправки кондиционеров ❄', 100],
                      ['549', 'Компрессоры ⛽', 100],
                      ['597', 'Пневмоинструмент 🎣', 100],
                      ['707', 'Пневмолинии 💨💧', 100],
                      ['623', 'Расходные материалы для автосервиса 📜🚗', 100],
                      ['946', 'Моечно-уборочное оборудование 🧹', 100],
                      ['493', 'АвтоХимия ☣⚗ ', 100],
                      ['580', 'Гаражное оборудование 👨🏾‍🔧', 100],
                      ['593', 'Диагностическое оборудование 🕵️‍♀', 100],
                      ['603', 'Маслосменное оборудование 💦🛢️', 100],
                      ['738', 'Электроинструмент 🔋', 100],
                      ['660', 'Сход/развалы 🔩📐', 100],
                      ['663', 'Мойки деталей 🛁', 100],
                      ['1095', 'Вытяжка отработанных газов ♨', 100],
                      ['692', 'Экспресс-сервис 🚅🤝🏻', 100],
                      ['688', 'Мебель для автосервиса 🗄️', 100],
                      ['702', 'Запчасти 🧩⚙️', 100],
                      ['1100', 'Автотовары 🍱', 100],
                      ['1101', 'Садовый инвентарь 👩‍🌾', 100]]
        self.calculater = {'1': '1⃣', '2': '2⃣', '3': '3⃣', '4': '4⃣', '5': '5⃣', '6': '6⃣', '7': '7⃣', '8': '8️⃣',
                           '9': '9⃣', 'minus': '➖', '0': '0️⃣', 'plus': '➕',
                           'back': '◀👈 Назад', 'delete': '⌫', 'done': 'Готово ✅🗑️',
                           'basket': f'Корзина 🛒(0 шт на 0 руб.)'}
        self.description_button = {'back': '◀ 👈 Назад', 'add': 'Добавить ✅🗑️',
                                   'basket': f'Корзина 🛒(0 шт на 0 руб.)'}

    @property
    def get_first_keyboard(self):
        return self.first_keyboard

    @property
    def get_prices(self):
        dict_price = {}
        for item in sorted(self.price, key=itemgetter(2), reverse=False):
            dict_price[item[0]] = item[1]
        return dict_price

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
    def get_pages_search(self):
        dict_pages_search = {}
        for item in range(100):
            dict_pages_search['Поиск_Стр.' + str(item)] = str(item)
        return dict_pages_search

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

    @property
    def get_price_creator(self):
        dict_price_creator = {}
        number = 1
        for item in sorted(self.price, key=itemgetter(2), reverse=False):
            dict_price_creator[item[0]] = item[1]
            dict_price_creator[f"level{item[0]}"] = f"Уровень{str(number)}"
            number += 1
        return dict_price_creator

    @staticmethod
    def get_category_creator(list_category: list):
        dict_category_creator = {}
        number = 1
        for item in sorted(list_category, key=itemgetter(2), reverse=False):
            dict_category_creator[item[0]] = item[1]
            dict_category_creator[f"level{item[0]}"] = f"Уровень{str(number)}"
            number += 1
        return dict_category_creator

    @property
    def get_levels_category(self):
        dict_levels = {}
        for item in range(400, 2000):
            dict_levels[f"level{str(item)}"] = str(item)
        return dict_levels

    @staticmethod
    def level_numbers(amount_nomenclatures: int):
        dict_numbers = {}
        for item in range(1, amount_nomenclatures + 1):
            dict_numbers[f"number_level{str(item)}"] = str(item)
        return dict_numbers

    @property
    def get_level_numbers(self):
        dict_level_numbers = {}
        for item in range(1, 200):
            dict_level_numbers[f"number_level{str(item)}"] = str(item)
        return dict_level_numbers

    def get_price_by_level(self, level: int):
        list_nomenclature = []
        for item in self.price:
            if item[2] == level:
                list_nomenclature.append(item[0])
        return list_nomenclature

    def set_price_level(self, kod_price: str, level: int):
        end_number = 1
        for item in sorted(self.price, key=itemgetter(2), reverse=False):
            if item[0] == kod_price:
                item[2] = level
            else:
                if end_number == level:
                    end_number += 1
                    item[2] = end_number
                    end_number += 1
                else:
                    item[2] = end_number
                    end_number += 1

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

    @property
    def get_basket_minus(self):
        dict_basket_minus = {}
        for item in range(4000, 30000):
            dict_basket_minus['basket_minus' + str(item)] = str(item)
        return dict_basket_minus

    @property
    def get_basket_plus(self):
        dict_basket_plus = {}
        for item in range(4000, 30000):
            dict_basket_plus['basket_plus' + str(item)] = str(item)
        return dict_basket_plus

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"

    @staticmethod
    def format_price(item: float):
        return '{0:,} ₽'.format(item).replace(',', ' ')


class USER:
    def __init__(self, id_user: int, in_queue: bool = False, last_admin: int = None):
        self.id_user = id_user
        self.in_queue = in_queue
        self.last_admin = last_admin
        self.list_message = []

    def add_message(self, message: Message, queue: Queue):
        if self.in_queue:
            self.list_message.append(message)
        else:
            self.in_queue = True
            queue.put(self)


class ADMIN:
    def __init__(self, admin_id: int):
        self.admin_id = admin_id


class MessageUser(StatesGroup):
    answer = State()
