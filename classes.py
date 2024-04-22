import asyncio
import logging
import re
import os
import openpyxl
import datetime
from data import DATA
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, FSInputFile, ChatPermissions
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
from aiogram.utils.media_group import MediaGroupBuilder
from operator import itemgetter
from openpyxl.styles import GradientFill

logging.basicConfig(level=logging.INFO)


class BotTelegram:
    def __init__(self, token_from_telegram):
        self.bot = BotMessage(token_from_telegram)
        self.dispatcher = DispatcherMessage(self.bot)
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

    async def send_message_order(self, chat_id: int, user: str, order: str, contact: str,
                                 keyboard: InlineKeyboardMarkup):
        return await self.send_document(chat_id=chat_id, document=FSInputFile(order),
                                        caption=f"От клиента {user} получен новый заказ! {contact}",
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
        self.data = DATA()
        self.execute = self.data.execute
        self.arr_auth_user = asyncio.run(self.execute.auth_user)
        self.first_keyboard = self.data.get_first_keyboard
        self.category = self.data.get_category
        self.nomenclatures = self.data.get_nomenclature
        self.pages = self.data.get_pages
        self.pages_search = self.data.get_pages_search
        self.dict_add = self.data.get_dict_value('add', 4000, 30000)
        self.dict_back_add = self.data.get_dict_value('back_add', 4000, 30000)
        self.dict_button_calculater = self.data.get_button_calculater
        self.dict_minus = self.data.get_dict_value('minus', 4000, 30000)
        self.dict_plus = self.data.get_dict_value('plus', 4000, 30000)
        self.dict_delete = self.data.get_dict_value('delete', 4000, 30000)
        self.dict_done = self.data.get_dict_value('done', 4000, 30000)
        self.button_basket_minus = self.data.get_dict_value('basket_minus', 4000, 30000)
        self.button_basket_plus = self.data.get_dict_value('basket_plus', 4000, 30000)
        self.choice_delivery = self.data.delivery
        self.kind_pickup = self.data.kind_pickup
        self.kind_delivery = self.data.kind_delivery

        @self.message(Command("help"))
        async def cmd_help(message: Message):
            await self.checking_bot(message)
            await self.help_message(message)
            await self.execute.add_element_history(message.from_user.id, 'help')
            await self.timer.start(message.from_user.id)

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            await self.checking_bot(message)
            first_keyboard = await self.data.get_first_keyboard(message.from_user.id)
            answer = await self.answer_message(message, "Выберете, что Вас интересует",
                                               self.build_keyboard(first_keyboard, 1))
            if await self.execute.start_message(message):
                await self.execute.restart_catalog(message, '/start')
                await self.execute.add_element_message(message.from_user.id, message.message_id)
            else:
                await self.execute.start_record_new_user(message)
                self.arr_auth_user[message.from_user.id] = None
            await self.delete_messages(message.from_user.id)
            await self.execute.add_element_message(message.from_user.id, answer.message_id)
            await self.timer.start(message.from_user.id)

        @self.message(Command("catalog"))
        async def cmd_catalog(message: Message):
            await self.checking_bot(message)
            menu_button = {'back': '◀ 👈 Назад'}
            answer = await self.bot.push_photo(message.chat.id, self.format_text("Каталог товаров ROSSVIK 📖"),
                                               self.build_keyboard(self.data.get_prices, 1, menu_button))
            await self.execute.add_element_message(message.from_user.id, message.message_id)
            await self.delete_messages(message.from_user.id)
            await self.execute.add_element_message(message.from_user.id, answer.message_id)
            await self.execute.restart_catalog(message, '/start catalog')
            await self.timer.start(message.from_user.id)

        @self.message(Command("news"))
        async def cmd_news(message: Message):
            await self.checking_bot(message)
            await self.show_link(message)
            await self.execute.add_element_history(message.from_user.id, 'news')
            await self.timer.start(message.from_user.id)

        @self.message(Command("basket"))
        async def cmd_basket(message: Message):
            await self.checking_bot(message)
            await self.show_basket_by_command(message, message.from_user.id)
            await self.execute.add_element_history(message.from_user.id, 'basket')
            await self.timer.start(message.from_user.id)

        @self.message(Command("order"))
        async def cmd_order(message: Message):
            await self.checking_bot(message)

        @self.message(F.from_user.id.in_(self.arr_auth_user) & F.content_type.in_({
            "text", "audio", "document", "photo", "sticker", "video", "video_note", "voice", "location", "contact",
            "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
            "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
            "migrate_from_chat_id", "pinned_message"}))
        async def get_message(message: Message):
            current_history = await self.execute.get_element_history(message.from_user.id, -1)
            if current_history in self.kind_pickup or current_history in self.kind_delivery:
                if message.content_type == "text":
                    try:
                        await self.record_message_comment_user(message)
                        await self.timer.start(message.from_user.id)
                    except IndexError:
                        await self.checking_bot(message)
                        await self.send_search_result(message)
            else:
                await self.checking_bot(message)
                await self.send_search_result(message)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'catalog'))
        async def send_catalog_message(callback: CallbackQuery):
            await self.catalog(callback)
            await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'answer_order'))
        async def answer_order_user(callback: CallbackQuery):
            print('answer')

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.category)))
        async def send_next_category(callback: CallbackQuery):
            if await self.next_category(callback):
                await self.execute.add_element_history(callback.from_user.id, callback.data)
            else:
                await self.execute.add_element_history(callback.from_user.id, f"{callback.data} Стр.1")
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages)))
        async def send_next_page(callback: CallbackQuery):
            if await self.next_page(callback):
                await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages_search)))
        async def send_next_page_search(callback: CallbackQuery):
            if await self.next_page_search(callback):
                await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.nomenclatures)))
        async def send_description(callback: CallbackQuery):
            await self.description(callback, callback.data)
            await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_add)))
        async def send_add(callback: CallbackQuery):
            await self.add_nomenclature(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_back_add)))
        async def send_back_add(callback: CallbackQuery):
            await self.back_add_nomenclature(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_button_calculater)))
        async def send_change_amount(callback: CallbackQuery):
            await self.change_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_minus)))
        async def send_change_minus(callback: CallbackQuery):
            await self.minus_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_plus)))
        async def send_change_plus(callback: CallbackQuery):
            await self.plus_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_delete)))
        async def send_change_delete(callback: CallbackQuery):
            await self.delete_amount(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_done)))
        async def send_done_basket(callback: CallbackQuery):
            await self.add_to_basket(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'basket'))
        async def send_show_basket(callback: CallbackQuery):
            await self.show_basket(callback)
            await self.execute.add_element_history(callback.from_user.id, callback.data)
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
            await self.execute.clean_basket(callback.from_user.id)
            await self.show_basket(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'post'))
        async def post_order(callback: CallbackQuery):
            list_history = await self.execute.get_arr_history(callback.from_user.id)
            await self.post_admin(callback, list_history[-2], list_history[-1])
            await self.execute.delete_element_history(callback.from_user.id, 3)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'choice_delivery'))
        async def send_choice_delivery(callback: CallbackQuery):
            await self.delete_messages(callback.from_user.id, callback.message.message_id)
            await self.choice_delivery_user(callback)
            await self.execute.add_element_history(callback.from_user.id, 'choice_delivery')
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.choice_delivery)))
        async def send_pickup_delivery(callback: CallbackQuery):
            if callback.data == 'pickup':
                await self.pickup(callback)
            elif callback.data == 'delivery':
                await self.delivery(callback)
            await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.kind_pickup)))
        async def send_kind_pickup(callback: CallbackQuery):
            await self.record_answer_pickup(callback)
            await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.kind_delivery)))
        async def send_kind_delivery(callback: CallbackQuery):
            await self.record_answer_delivery(callback)
            await self.execute.add_element_history(callback.from_user.id, callback.data)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'choice_contact'))
        async def send_choice_contact(callback: CallbackQuery):
            await self.choice_comment_user(callback)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'back'))
        async def send_return_message(callback: CallbackQuery):
            current = await self.execute.delete_element_history(callback.from_user.id, 1)
            if 'search' in current:
                current = await self.execute.delete_element_history(callback.from_user.id, 1)
            if current == '/start':
                await self.return_start(callback)
                await self.timer.start(callback.from_user.id)
            elif current == 'catalog':
                await self.catalog(callback)
                await self.timer.start(callback.from_user.id)
            elif current == 'help':
                await self.return_help_message(callback)
                await self.timer.start(callback.from_user.id)
            elif current == 'news':
                await self.return_show_link(callback)
                await self.timer.start(callback.from_user.id)
            elif current in self.category:
                await self.return_category(callback, current)
                await self.timer.start(callback.from_user.id)
            elif current in self.pages:
                await self.return_page(callback, current)
                await self.execute.add_element_history(callback.from_user.id, current)
                await self.timer.start(callback.from_user.id)
            elif current in self.nomenclatures:
                await self.description(callback, current)
                await self.timer.start(callback.from_user.id)
            elif current in self.pages_search:
                previous_history = await self.execute.delete_element_history(callback.from_user.id, 1)
                result_search = await self.search(self.get_text_for_search(previous_history.split('___')[1]))
                await self.return_page_search(callback, result_search, current)
                await self.execute.add_element_history(callback.from_user.id, current)
                await self.timer.start(callback.from_user.id)
            elif current == 'basket':
                await self.show_basket(callback)
                await self.timer.start(callback.from_user.id)
            elif current == 'choice_delivery':
                await self.choice_delivery_user(callback)
                await self.timer.start(callback.from_user.id)
            elif current in self.choice_delivery:
                if current == 'pickup':
                    await self.pickup(callback)
                elif current == 'delivery':
                    await self.delivery(callback)
                await self.timer.start(callback.from_user.id)

    async def checking_bot(self, message: Message):
        if message.from_user.is_bot:
            await self.bot.restrict_chat_member(message.chat.id, message.from_user.id, ChatPermissions())

    async def help_message(self, message: Message):
        whitespace = '\n'
        first_keyboard = await self.data.get_first_keyboard(message.from_user.id)
        answer = await self.answer_message(message, f"Вы можете воспользоваться быстрой навигацией,"
                                                    f"отправляя следующие команды:{whitespace}{whitespace}"
                                                    f"/start - главное меню{whitespace}"
                                                    f"/catalog - каталог товара{whitespace}"
                                                    f"/news - новости{whitespace}"
                                                    f"/basket - корзина{whitespace}"
                                                    f"/order - история заказов{whitespace}{whitespace}"
                                                    f"Поиск товара:{whitespace}{whitespace}"
                                                    f"При отправке боту сообщения происходит поиск товара в каталоге "
                                                    f"по содержимому сообщения, разделенному пробелами. Можно "
                                                    f"указывать не только слова, но и символы, которые содержатся, "
                                                    f"например, в наименовании товара.{whitespace}Чтобы понять, "
                                                    f"как это работает, попробуйте отправить боту "
                                                    f"сообщение:{whitespace}пласт вст{whitespace}{whitespace}"
                                                    f"УВЕДОМЛЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ: Все данные, полученные в "
                                                    f"процессе взаимодействия между Ботом и Пользователем: фото, "
                                                    f"видео, текстовая информация, а также любые отправленные "
                                                    f"документы, которые содержат конфиденциальную информацию не "
                                                    f"подлежат использованию, копированию, распространению, "
                                                    f"а также осуществлению любых других действий "
                                                    f"на основе этой информации.",
                                           self.build_keyboard(first_keyboard, 1))
        await self.execute.add_element_message(message.from_user.id, message.message_id)
        await self.delete_messages(message.from_user.id)
        await self.execute.add_element_message(message.from_user.id, answer.message_id)

    async def return_help_message(self, call_back: CallbackQuery):
        whitespace = '\n'
        first_keyboard = await self.data.get_first_keyboard(call_back.from_user.id)
        answer = await self.answer_message(call_back.message,
                                           f"Вы можете воспользоваться быстрой навигацией,"
                                           f"отправляя следующие команды:{whitespace}{whitespace}"
                                           f"/start - главное меню{whitespace}"
                                           f"/catalog - каталог товара{whitespace}"
                                           f"/news - новости{whitespace}"
                                           f"/basket - корзина{whitespace}"
                                           f"/order - история заказов{whitespace}{whitespace}"
                                           f"Поиск товара:{whitespace}{whitespace}"
                                           f"При отправке боту сообщения происходит поиск товара в каталоге "
                                           f"по содержимому сообщения, разделенному пробелами. Можно "
                                           f"указывать не только слова, но и символы, которые содержатся, "
                                           f"например, в наименовании товара.{whitespace}Чтобы понять, "
                                           f"как это работает, попробуйте отправить боту "
                                           f"сообщение:{whitespace}пласт вст{whitespace}{whitespace}"
                                           f"УВЕДОМЛЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ: Все данные, полученные в "
                                           f"процессе взаимодействия между Ботом и Пользователем: фото, "
                                           f"видео, текстовая информация, а также любые отправленные "
                                           f"документы, которые содержат конфиденциальную информацию не "
                                           f"подлежат использованию, копированию, распространению, "
                                           f"а также осуществлению любых других действий "
                                           f"на основе этой информации.",
                                           self.build_keyboard(first_keyboard, 1))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def return_start(self, call_back: CallbackQuery):
        first_keyboard = await self.data.get_first_keyboard(call_back.from_user.id)
        answer = await self.answer_message(call_back.message, "Выберете, что Вас интересует",
                                           self.build_keyboard(first_keyboard, 1))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def catalog(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.bot.push_photo(call_back.message.chat.id, self.format_text("Каталог товаров ROSSVIK 📖"),
                                           self.build_keyboard(self.data.get_prices, 1, menu_button))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def show_link(self, message: Message):
        link_keyboard = {'https://t.me/rossvik_moscow': 'Канал @ROSSVIK_MOSCOW 📣💬',
                         'https://www.rossvik.moscow/': 'Сайт WWW.ROSSVIK.MOSCOW 🌐', 'back': '◀ 👈 Назад'}
        answer = await self.answer_message(message, f"Перейдите по ссылкам ниже, чтобы узнать ещё больше информации:",
                                           self.build_keyboard(link_keyboard, 1))
        await self.execute.add_element_message(message.from_user.id, message.message_id)
        await self.delete_messages(message.from_user.id)
        await self.execute.add_element_message(message.from_user.id, answer.message_id)

    async def return_show_link(self, call_back: CallbackQuery):
        link_keyboard = {'https://t.me/rossvik_moscow': 'Канал @ROSSVIK_MOSCOW 📣💬',
                         'https://www.rossvik.moscow/': 'Сайт WWW.ROSSVIK.MOSCOW 🌐', 'back': '◀ 👈 Назад'}
        answer = await self.answer_message(call_back.message, f"Перейдите по ссылкам ниже, "
                                                              f"чтобы узнать ещё больше информации:",
                                           self.build_keyboard(link_keyboard, 1))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def next_category(self, call_back: CallbackQuery):
        current_category = await self.execute.current_category(call_back.data)
        if current_category:
            await self.create_keyboard_edit_caption(call_back, current_category, call_back.data)
            return True
        else:
            await self.list_nomenclature(call_back)
            return False

    async def return_category(self, call_back: CallbackQuery, current_history):
        current_category = await self.execute.current_category(current_history)
        if current_category:
            try:
                await self.create_keyboard_edit_caption(call_back, current_category, current_history)
            except TelegramBadRequest:
                await self.create_keyboard_push_photo(call_back, current_category, current_history)
        else:
            new_current = await self.execute.delete_element_history(call_back.from_user.id, 1)
            if new_current == 'catalog':
                if call_back.message.caption:
                    answer_message = await self.create_price_edit_caption(call_back)
                    await self.delete_messages(call_back.from_user.id, answer_message.message_id)
                else:
                    await self.catalog(call_back)
            else:
                current_category = await self.execute.current_category(new_current)
                await self.create_keyboard_push_photo(call_back, current_category, new_current)

    async def list_nomenclature(self, call_back: CallbackQuery):
        number_page = '\n' + 'Страница №1'
        current_nomenclature = await self.execute.current_nomenclature(call_back.data)
        pages = {}
        for page in current_nomenclature.keys():
            pages[page] = page
        text = await self.execute.text_category(call_back.data)
        heading = await self.edit_caption(call_back.message,
                                          self.format_text(text + number_page),
                                          self.build_keyboard(pages, 5))
        arr_answers = []
        for key, value in current_nomenclature['Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

    async def description(self, call_back: CallbackQuery, id_nomenclature: str):
        current_description = await self.description_nomenclature(id_nomenclature, call_back.from_user.id,
                                                                  call_back.id)
        arr_answer = await self.send_photo(call_back.message, current_description[0], current_description[1])
        basket = await self.data.get_basket(call_back.from_user.id)
        menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️', 'basket': basket['basket']}
        answer_description = await self.answer_message(arr_answer[0], current_description[2],
                                                       self.build_keyboard(menu_button, 2))
        arr_answer.append(answer_description)
        arr_message = []
        for item_message in arr_answer:
            arr_message.append(str(item_message.message_id))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_arr_messages(call_back.from_user.id, arr_message)

    async def description_nomenclature(self, id_item: str, id_user: int, id_call_back: str):
        whitespace = '\n'
        arr_description = await self.execute.current_description(id_item)
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

    async def next_page(self, call_back: CallbackQuery):
        if self.pages[call_back.data] == call_back.message.caption.split('№')[1]:
            return False
        else:
            id_category = await self.execute.delete_element_history(call_back.from_user.id, 1)
            current_nomenclature = await self.execute.current_nomenclature(id_category)
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
                menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
                answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
            return True

    async def return_page(self, call_back: CallbackQuery, current_page: str):
        number_page = '\n' + 'Страница №' + self.pages[current_page]
        id_category = await self.execute.delete_element_history(call_back.from_user.id, 1)
        current_nomenclature = await self.execute.current_nomenclature(id_category)
        text = await self.execute.text_category(id_category)
        pages = {}
        for page in current_nomenclature.keys():
            pages[page] = page
        heading = await self.bot.push_photo(call_back.message.chat.id, self.format_text(text + number_page),
                                            self.build_keyboard(pages, 5))
        await self.delete_messages(call_back.from_user.id)
        await asyncio.sleep(0.5)
        arr_answers = [str(heading.message_id)]
        for key, value in current_nomenclature[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

    async def add_nomenclature(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_add[call_back.data]
        arr_description = await self.execute.current_description(id_nomenclature)
        current_history = await self.execute.get_element_history(call_back.from_user.id, -1)
        if current_history in self.nomenclatures:
            info_nomenclature = f'Введите количество, которое нужно добавить в корзину:{whitespace}'
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        else:
            availability = self.get_availability(arr_description[7])
            if self.arr_auth_user[call_back.from_user.id] == 'diler':
                dealer = self.get_dealer(arr_description[8], arr_description[9])
                info_nomenclature = f'{self.format_text(arr_description[2])}{whitespace}' \
                                    f'Цена: {self.format_text(self.format_price(float(arr_description[8])))}' \
                                    f'{whitespace}' \
                                    f'Дилерская цена: {self.format_text(self.format_price(float(dealer)))}' \
                                    f'{whitespace}' \
                                    f'Наличие: {self.format_text(availability)}{whitespace}' \
                                    f'Введите количество, которое нужно добавить в корзину:{whitespace}'
            else:
                info_nomenclature = f'{self.format_text(arr_description[2])}{whitespace}' \
                                    f'Цена: {self.format_text(self.format_price(float(arr_description[8])))}' \
                                    f'{whitespace}' \
                                    f'Наличие: {self.format_text(availability)}{whitespace}' \
                                    f'Введите количество, которое нужно добавить в корзину:{whitespace}'
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        await self.edit_message(call_back.message, info_nomenclature, self.build_keyboard(menu_button, 3))

    async def back_add_nomenclature(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_back_add[call_back.data]
        arr_description = await self.execute.current_description(id_nomenclature)
        current_history = await self.execute.get_element_history(call_back.from_user.id, -1)
        if current_history in self.dict_add:
            info_nomenclature = f'{arr_description[4]}{whitespace}' \
                                f'{arr_description[5]}'
            if re.sub('\W+', '', info_nomenclature) == "":
                info_nomenclature = "Нет подробной информации"
            basket = await self.data.get_basket(call_back.from_user.id)
            menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️', 'basket': basket['basket']}
            await self.execute.delete_element_history(call_back.from_user.id, 1)
        else:
            info_nomenclature = f'{self.format_text(arr_description[2])}'
            menu_button = {'back': '◀ 👈 Назад', id_nomenclature: 'Подробнее 👀📸',
                           f'{id_nomenclature}add': 'Добавить ✅🗑️'}
        await self.edit_message(call_back.message, info_nomenclature, self.build_keyboard(menu_button, 2))

    async def change_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        button = self.dict_button_calculater[call_back.data]
        id_nomenclature = call_back.data.split('///')[0]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        amount = self.get_amount(call_back.message.text, button)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        sum_nomenclature = float(amount) * float(price)
        text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
               f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
        try:
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
        except TelegramBadRequest as error:
            print(error)

    async def minus_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_minus[call_back.data]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        amount = self.get_amount_minus(call_back.message.text)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                print(error)
        else:
            pass

    async def plus_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_plus[call_back.data]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        amount = self.get_amount_plus(call_back.message.text)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                print(error)
        else:
            pass

    async def delete_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_delete[call_back.data]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        amount = self.get_amount_delete(call_back.message.text)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
            except TelegramBadRequest as error:
                print(error)
        else:
            pass

    async def add_to_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_done[call_back.data]
        arr_description = await self.execute.current_description(id_nomenclature)
        amount = await self.check_amount(call_back.message.text, call_back.id, arr_description[7])
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            basket = await self.execute.current_basket_dict(call_back.from_user.id)
            basket[id_nomenclature] = [amount, sum_nomenclature]
            await self.execute.add_basket_product(call_back.from_user.id, self.assembling_basket_dict(basket))
            text = f"Вы добавили {arr_description[2]} в количестве:{whitespace}" \
                   f"{amount} шт. на сумму {self.format_price(float(sum_nomenclature))} в корзину."
            basket = await self.data.get_basket(call_back.from_user.id)
            current_history = await self.execute.get_element_history(call_back.from_user.id, -1)
            if current_history in self.dict_add:
                menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️',
                               'basket': basket['basket']}
                await self.execute.delete_element_history(call_back.from_user.id, 1)
            else:
                menu_button = {'back': '◀ 👈 Назад', id_nomenclature: 'Подробнее 👀📸',
                               f'{id_nomenclature}add': 'Добавить ✅🗑️'}
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            except TelegramBadRequest as error:
                print(error)
        else:
            pass

    async def check_amount(self, text_message: str, id_call_back: str, amount_in_base: str):
        whitespace = '\n'
        if amount_in_base == 'Нет на складе':
            amount_in_base = '0'
        arr_string = text_message.split(whitespace)
        if len(arr_string) == 2:
            amount = arr_string[1].split(' шт')[0]
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

    @staticmethod
    def get_availability(amount: str):
        if amount == "0":
            availability = "Нет на складе"
        else:
            availability = amount
        return availability

    @staticmethod
    def get_dealer(price: str, dealer: str):
        if any([dealer is None, dealer == '', dealer == '0']):
            value = price
        else:
            value = dealer
        return value

    @staticmethod
    def get_amount(text_message: str, button: str):
        whitespace = '\n'
        arr_string = text_message.split(whitespace)
        if len(arr_string) == 2:
            amount = f"{arr_string[1].split(' шт')[0]}{button}"
        else:
            amount = button
        if amount[0] == '0':
            amount = button
        return amount

    @staticmethod
    def get_amount_minus(text_message: str):
        whitespace = '\n'
        arr_string = text_message.split(whitespace)
        if len(arr_string) == 2:
            amount = arr_string[1].split(' шт')[0]
            if int(amount) == 0:
                amount = 0
            else:
                amount = int(amount) - 1
        else:
            amount = None
        return amount

    @staticmethod
    def get_amount_plus(text_message: str):
        whitespace = '\n'
        arr_string = text_message.split(whitespace)
        if len(arr_string) == 2:
            amount = arr_string[1].split(' шт')[0]
            if int(amount) == 0:
                amount = 1
            else:
                amount = int(amount) + 1
        else:
            amount = None
        return amount

    @staticmethod
    def get_amount_delete(text_message: str):
        whitespace = '\n'
        arr_string = text_message.split(whitespace)
        if len(arr_string) == 2:
            amount = arr_string[1].split(' шт')[0]
            if len(amount) > 1:
                amount = amount[:-1]
            else:
                amount = 0
        else:
            amount = None
        return amount

    async def show_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket_dict = await self.execute.current_basket_dict(call_back.from_user.id)
        if len(current_basket_dict) == 0:
            text = 'Ваша корзина пуста 😭😔💔'
            menu_button = {'back': '◀ 👈 Назад'}
            answer = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 1))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        else:
            sum_basket = self.sum_basket(current_basket_dict)
            text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                           'choice_delivery': 'Оформить заказ 📧📦📲'}
            heading = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            await self.delete_messages(call_back.from_user.id, heading.message_id)
            arr_answers = []
            for key, item in current_basket_dict.items():
                name = await self.execute.current_description(key)
                text = f"{name[2]}:{whitespace}{item[0]} шт. на сумму {self.format_price(float(item[1]))}"
                menu_button = {f'{key}basket_minus': '➖', f'{key}basket_plus': '➕'}
                answer = await self.answer_message(heading, text, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

    async def show_basket_by_command(self, message: Message, id_user: int):
        whitespace = '\n'
        current_basket_dict = await self.execute.current_basket_dict(id_user)
        if len(current_basket_dict) == 0:
            text = 'Ваша корзина пуста 😭😔💔'
            menu_button = {'back': '◀ 👈 Назад'}
            answer = await self.answer_message(message, text, self.build_keyboard(menu_button, 1))
            await self.execute.add_element_message(message.from_user.id, message.message_id)
            await self.delete_messages(message.from_user.id)
            await self.execute.add_element_message(message.from_user.id, answer.message_id)
        else:
            sum_basket = self.sum_basket(current_basket_dict)
            text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                           'choice_delivery': 'Оформить заказ 📧📦📲'}
            heading = await self.answer_message(message, text, self.build_keyboard(menu_button, 2))
            await self.execute.add_element_message(message.from_user.id, message.message_id)
            await self.delete_messages(message.from_user.id)
            await self.execute.add_element_message(message.from_user.id, heading.message_id)
            arr_answers = []
            for key, item in current_basket_dict.items():
                name = await self.execute.current_description(key)
                text = f"{name[2]}:{whitespace}{item[0]} шт. на сумму {self.format_price(float(item[1]))}"
                menu_button = {f'{key}basket_minus': '➖', f'{key}basket_plus': '➕'}
                answer = await self.answer_message(heading, text, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            await self.execute.add_arr_messages(message.from_user.id, arr_answers)

    async def minus_amount_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket_dict = await self.execute.current_basket_dict(call_back.from_user.id)
        current_amount = float(current_basket_dict[self.button_basket_minus[call_back.data]][0])
        price = float(current_basket_dict[self.button_basket_minus[call_back.data]][1]) / float(current_amount)
        if current_amount > 1:
            current_amount -= 1
            current_basket_dict[self.button_basket_minus[call_back.data]] = [str(current_amount),
                                                                             str(price * current_amount)]
            await self.execute.add_basket_product(call_back.from_user.id,
                                                  self.assembling_basket_dict(current_basket_dict))
            name = await self.execute.current_description(self.button_basket_minus[call_back.data])
            text = f"{name[2]}:{whitespace}{int(current_amount)} шт. на сумму " \
                   f"{self.format_price(price * current_amount)}"
            menu_button = {f'{self.button_basket_minus[call_back.data]}basket_minus': '➖',
                           f'{self.button_basket_minus[call_back.data]}basket_plus': '➕'}
            sum_basket = self.sum_basket(current_basket_dict)
            head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            head_menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                'choice_delivery': 'Оформить заказ 📧📦📲'}
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
            await self.bot.edit_head_message(head_text, call_back.message.chat.id, arr_messages[0],
                                             self.build_keyboard(head_menu_button, 2))
        else:
            current_basket_dict.pop(self.button_basket_minus[call_back.data])
            if len(current_basket_dict) == 0:
                await self.execute.clean_basket(call_back.from_user.id)
                await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
                head_text = 'Ваша корзина пуста 😭😔💔'
                head_menu_button = {'back': '◀ 👈 Назад'}
                arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
                await self.bot.edit_head_message(head_text, call_back.message.chat.id, arr_messages[0],
                                                 self.build_keyboard(head_menu_button, 1))
            else:
                await self.execute.add_basket_product(call_back.from_user.id,
                                                      self.assembling_basket_dict(current_basket_dict))
                await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
                sum_basket = self.sum_basket(current_basket_dict)
                head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                            f"{self.format_price(float(sum_basket))}:"
                head_menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                    'choice_delivery': 'Оформить заказ 📧📦📲'}
                arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
                await self.bot.edit_head_message(head_text, call_back.message.chat.id,
                                                 arr_messages[0],
                                                 self.build_keyboard(head_menu_button, 2))

    async def plus_amount_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        current_basket_dict = await self.execute.current_basket_dict(call_back.from_user.id)
        current_amount = float(current_basket_dict[self.button_basket_plus[call_back.data]][0])
        price = float(current_basket_dict[self.button_basket_plus[call_back.data]][1]) / float(current_amount)
        availability = await self.execute.current_description(self.button_basket_plus[call_back.data])
        if str(int(current_amount)) == availability[7] or availability[7] == "Нет на складе":
            await self.bot.alert_message(call_back.id, 'Нельзя добавить товара больше, чем есть на остатках!')
        else:
            current_amount += 1
            current_basket_dict[self.button_basket_plus[call_back.data]] = [str(current_amount),
                                                                            str(price * current_amount)]
            await self.execute.add_basket_product(call_back.from_user.id,
                                                  self.assembling_basket_dict(current_basket_dict))
            name = await self.execute.current_description(self.button_basket_plus[call_back.data])
            text = f"{name[2]}:{whitespace}{int(current_amount)} шт. на сумму " \
                   f"{self.format_price(price * current_amount)}"
            menu_button = {f'{self.button_basket_plus[call_back.data]}basket_minus': '➖',
                           f'{self.button_basket_plus[call_back.data]}basket_plus': '➕'}
            sum_basket = self.sum_basket(current_basket_dict)
            head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму {self.format_price(float(sum_basket))}:"
            head_menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                'choice_delivery': 'Оформить заказ 📧📦📲'}
            await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2))
            arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
            await self.bot.edit_head_message(head_text, call_back.message.chat.id, arr_messages[0],
                                             self.build_keyboard(head_menu_button, 2))

    @staticmethod
    def assembling_basket_dict(basket_dict: dict):
        list_basket = []
        for key, value in basket_dict.items():
            item = f'{key}///{value[0]}///{value[1]}'
            list_basket.append(item)
        return ' '.join(list_basket)

    @staticmethod
    def assembling_basket_dict_for_order(basket_dict: dict):
        list_basket = []
        for key, value in basket_dict.items():
            item = f'{key}///{value[0]}///{value[1]}'
            list_basket.append(item)
        return '_____'.join(list_basket)

    @staticmethod
    def get_dict_basket_for_order(basket_str: str):
        basket_dict = {}
        if basket_str is None:
            basket_dict = {}
        else:
            for item in basket_str.split('_____'):
                row = item.split('///')
                basket_dict[row[0]] = [row[1], row[2]]
        return basket_dict

    @staticmethod
    def sum_basket(current_basket: dict):
        sum_item = 0
        for item in current_basket.values():
            sum_item += float(item[1])
        return sum_item

    async def search(self, text: str):
        total_search = set()
        i = 1
        for item in self.change_for_search_name(text):
            if i == 1:
                search_variant = await self.execute.search_in_base_article(
                    self.translit_rus(re.sub('\W+', '', item[0]).upper()))
                for variant in item:
                    search_result_by_name = await self.execute.search_in_base_name(variant)
                    search_variant.update(search_result_by_name)
                total_search = search_variant
                i += 1
            else:
                search_variant = await self.execute.search_in_base_article(
                    self.translit_rus(re.sub('\W+', '', item[0]).upper()))
                for variant in item:
                    search_result_by_name = await self.execute.search_in_base_name(variant)
                    search_variant.update(search_result_by_name)
                total_search = total_search.intersection(search_variant)
                i += 1
        return self.assembling_search(list(total_search))

    async def send_search_result(self, message: Message):
        id_user = message.from_user.id
        result_search = await self.search(message.text)
        current_history = await self.execute.get_element_history(id_user, -1)
        if len(result_search['Поиск_Стр.1']) == 0:
            await self.find_nothing(id_user, message)
            if 'search' in current_history:
                await self.timer.start(id_user)
            elif 'Поиск' in current_history:
                await self.execute.delete_element_history(id_user, 1)
                await self.timer.start(id_user)
            else:
                await self.execute.add_element_history(id_user, f'search___{self.change_record_search(message.text)}')
                await self.timer.start(id_user)
        else:
            await self.show_result_search(id_user, message, result_search)
            if 'search' in current_history:
                await self.execute.delete_element_history(id_user, 1)
                await self.execute.add_element_history(id_user,
                                                       f"search___{self.change_record_search(message.text)} "
                                                       f"Поиск_Стр.1")
                await self.timer.start(id_user)
            elif 'Поиск' in current_history:
                await self.execute.delete_element_history(id_user, 2)
                await self.execute.add_element_history(id_user,
                                                       f"search___{self.change_record_search(message.text)} "
                                                       f"Поиск_Стр.1")
                await self.timer.start(id_user)
            else:
                await self.execute.add_element_history(id_user,
                                                       f"search___{self.change_record_search(message.text)} "
                                                       f"Поиск_Стр.1")
                await self.timer.start(id_user)

    async def find_nothing(self, id_user: int, message: Message):
        await self.execute.add_element_message(id_user, message.message_id)
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.answer_message(message, "Сожалеем, но ничего не найдено.",
                                           self.build_keyboard(menu_button, 1))
        await self.delete_messages(id_user)
        await self.execute.add_element_message(id_user, answer.message_id)

    async def show_result_search(self, id_user: int, message: Message, result_search: dict):
        await self.execute.add_element_message(id_user, message.message_id)
        number_page = '\n' + 'Страница №1'
        pages = {}
        for page in result_search.keys():
            pages[page] = page
        heading = await self.answer_message(message, self.format_text(f"Результаты поиска:{number_page}"),
                                            self.build_keyboard(pages, 3))
        await self.delete_messages(id_user)
        arr_answers = [str(heading.message_id)]
        for key, value in result_search['Поиск_Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(id_user, arr_answers)

    async def next_page_search(self, call_back: CallbackQuery):
        if self.pages_search[call_back.data] == call_back.message.text.split('№')[1]:
            return False
        else:
            previous_history = await self.execute.delete_element_history(call_back.from_user.id, 1)
            result_search = await self.search(self.get_text_for_search(previous_history.split('___')[1]))
            pages = {}
            for page in result_search.keys():
                pages[page] = page
            heading = await self.edit_message(call_back.message,
                                              f"{call_back.message.text.split('№')[0]}"
                                              f"№{self.pages_search[call_back.data]}",
                                              self.build_keyboard(pages, 3))
            await self.delete_messages(call_back.from_user.id, heading.message_id)
            arr_answers = []
            for key, value in result_search[call_back.data].items():
                menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
                answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
            return True

    async def return_page_search(self, call_back: CallbackQuery, result_search: dict, current_page: str):
        number_page = '\n' + 'Страница №' + self.pages_search[current_page]
        pages = {}
        for page in result_search.keys():
            pages[page] = page
        heading = await self.edit_message(call_back.message,
                                          self.format_text(f"Результаты поиска:{number_page}"),
                                          self.build_keyboard(pages, 3))
        await self.delete_messages(call_back.from_user.id, heading.message_id)
        await asyncio.sleep(0.5)
        arr_answers = []
        for key, value in result_search[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            answer = await self.answer_message(heading, value, self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

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
    def change_for_search_name(text_cross: str):
        text_list = text_cross.split()
        new_text_list = []
        for item in text_list:
            if re.sub('\W+', '', item) != '':
                new_text_list.append([item, item.lower(), item.title()])
        return new_text_list

    @staticmethod
    def change_record_search(text: str):
        list_record = text.split()
        return '/////'.join(list_record)

    @staticmethod
    def get_text_for_search(text: str):
        list_search = text.split('/////')
        return ' '.join(list_search)

    async def post_admin(self, call_back: CallbackQuery, value_delivery: str, kind_delivery: str):
        current_basket_dict = await self.execute.current_basket_dict(call_back.from_user.id)
        order = await self.save_order(call_back, current_basket_dict)
        number_order = order[0]
        order_dict = order[1]
        list_user_admin = await self.execute.get_user_admin
        menu_button = {'take_order': '💬 Взять заказ в обработку'}
        delivery_address_from_user = await self.execute.get_delivery_address(call_back.from_user.id)
        if delivery_address_from_user is None:
            delivery_address_from_user = 'Частное лицо'
        arr_messages_from_user = self.get_arr_message_user(delivery_address_from_user)
        change_contact = await self.set_new_contact(call_back.from_user.id, value_delivery, kind_delivery,
                                                    '\n'.join(arr_messages_from_user))
        order_dict[number_order]['contact_order'] = delivery_address_from_user
        current_contact = '\n'.join(order_dict[number_order]['contact_order'].split('/////'))
        if value_delivery == 'pickup':
            value_d = self.choice_delivery[value_delivery]
            kind_d = self.kind_pickup[kind_delivery]
        else:
            value_d = self.choice_delivery[value_delivery]
            kind_d = self.kind_delivery[kind_delivery]
        list_messages_admins = []
        for user in list_user_admin:
            answer = await self.bot.send_message_order(int(user[0]),
                                                       f'{call_back.from_user.id} '
                                                       f'{call_back.from_user.first_name} '
                                                       f'{call_back.from_user.last_name} ',
                                                       order_dict[number_order]['path_order'],
                                                       f"{value_d}\n{kind_d}\n{current_contact}",
                                                       self.build_keyboard(menu_button, 1))
            list_messages_admins.append(str(answer.message_id))
        order_dict[number_order]['id_message_admins'] = list_messages_admins
        await self.execute.record_contact(call_back.from_user.id, change_contact)
        await self.record_order_base(call_back, order_dict)
        await self.execute.clean_basket(call_back.from_user.id)
        await self.execute.clean_delivery(call_back.from_user.id)
        text = 'Мы получили заказ, в ближайшее время пришлем Вам счет для оплаты или свяжемся с Вами, ' \
               'если у нас появятся вопросы 😎👌🔥'
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)

    async def choice_delivery_user(self, call_back: CallbackQuery):
        head_menu_button = {'pickup': 'Самовывоз 🖐🏻', 'delivery': 'Доставка 📦', 'back': '◀ 👈 Назад'}
        head_text = f"Выберете вариант получения товара:"
        answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)

    async def pickup(self, call_back: CallbackQuery):
        head_menu_button = {'record_answer_shop': 'Москва, Хачатуряна, 8 корпус 3 (Магазин)',
                            'record_answer_storage': 'Мытищи, 1-ая Новая, 57 (Склад)',
                            'back': '◀ 👈 Назад'}
        head_text = f"Выберете откуда будете забирать товар:"
        answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)

    async def delivery(self, call_back: CallbackQuery):
        head_menu_button = {'record_answer_moscow': 'В пределах МКАД',
                            'record_answer_pek': 'ТК ПЭК',
                            'record_answer_dl': 'ТК Деловые Линии',
                            'record_answer_mt': 'ТК Мейджик Транс',
                            'record_answer_cdek': 'ТК СДЭК',
                            'back': '◀ 👈 Назад'}
        head_text = f"Выберете какой транспортной компанией доставить товар, " \
                    f"либо можем доставить товар своими силами в пределах МКАД:"
        answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)

    async def record_answer_pickup(self, call_back: CallbackQuery):
        whitespace = '\n'
        arr_contact = await self.execute.get_arr_contact(call_back.from_user.id)
        dict_contact = self.get_dict_contact(arr_contact)
        head_menu_button = {'back': '◀ 👈 Назад', 'post': 'Отправить заказ 📫'}
        if dict_contact['pickup'][call_back.data][0] == 'empty':
            head_text = f"{call_back.from_user.first_name} {call_back.from_user.last_name} у нас нет контактных " \
                        f"данных по Вашей учетной записи. Мы можем выставить счет на Частное лицо или отправьте нам " \
                        f"сообщение с Вашими реквизитами, например:{whitespace}ООО «Алькар»{whitespace}" \
                        f"ИНН 9715341213 КПП 771501001{whitespace}Юридический, фактический и почтовый адрес: " \
                        f"127562, город Москва, улица Хачатуряна, дом 8, корпус 3, комн. 15{whitespace}" \
                        f"Тел. +7 (495) 215-000-3, 8 (800) 333-22-60{whitespace}Почта info@rossvik.moscow{whitespace}" \
                        f"Приеду во вторник!"
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 2))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        else:
            menu_contact = {'choice_contact': 'Выбрать эти реквизиты ✅', 'delete_record': 'Удалить запись 🗑️'}
            head_text = f"Мы сохранили информацию, которую Вы нам отправляли при предыдущих заказах.{whitespace}" \
                        f"Можете выбрать из списка ниже или отправить нам новые реквизиты и комментарии одним или " \
                        f"несколькими сообщениями."
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 2))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
            arr_answers = []
            for contact in dict_contact['pickup'][call_back.data]:
                answer_contact = await self.answer_message(answer, contact, self.build_keyboard(menu_contact, 1))
                arr_answers.append(str(answer_contact.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
            await self.execute.clean_delivery(call_back.from_user.id)

    async def record_answer_delivery(self, call_back: CallbackQuery):
        whitespace = '\n'
        arr_contact = await self.execute.get_arr_contact(call_back.from_user.id)
        dict_contact = self.get_dict_contact(arr_contact)
        head_menu_button = {'back': '◀ 👈 Назад', 'post': 'Отправить заказ 📫'}
        if dict_contact['delivery'][call_back.data][0] == 'empty':
            head_text = f"{call_back.from_user.first_name} {call_back.from_user.last_name} у нас нет контактных " \
                        f"данных по Вашей учетной записи. Мы можем выставить счет на Частное лицо или отправьте нам " \
                        f"сообщение с Вашими реквизитами, например:{whitespace}ООО «Алькар»{whitespace}" \
                        f"ИНН 9715341213 КПП 771501001{whitespace}Юридический, фактический и почтовый адрес: " \
                        f"127562, город Москва, улица Хачатуряна, дом 8, корпус 3, комн. 15{whitespace}" \
                        f"Тел. +7 (495) 215-000-3, 8 (800) 333-22-60{whitespace}Почта info@rossvik.moscow{whitespace}" \
                        f"Адрес доставки: Мытищи, 1-ая Новая, 57{whitespace}" \
                        f"Режим работы: 9:00 - 20:00"
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 2))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        else:
            menu_contact = {'choice_contact': 'Выбрать эти реквизиты ☑', 'delete_record': 'Удалить запись 🗑️'}
            head_text = f"Мы сохранили информацию, которую Вы нам отправляли при предыдущих заказах.{whitespace}" \
                        f"Можете выбрать из списка ниже или отправить нам новые реквизиты и комментарии одним или " \
                        f"несколькими сообщениями. Например:{whitespace}" \
                        f"Шиномонтаж на Красной площади{whitespace}" \
                        f"Адрес: Москва, ул Тверская, д 10{whitespace}" \
                        f"Режим работы: 9:00 - 20:00"
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 2))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
            arr_answers = []
            for contact in dict_contact['delivery'][call_back.data]:
                answer_contact = await self.answer_message(answer, contact, self.build_keyboard(menu_contact, 1))
                arr_answers.append(str(answer_contact.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
            await self.execute.clean_delivery(call_back.from_user.id)

    async def record_message_comment_user(self, message: Message):
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        head_message = arr_messages[0]
        await self.delete_messages(message.from_user.id, head_message)
        arr_message = [str(message.message_id)]
        change_text = f"Сообщение получено"
        answer = await self.answer_text(message, change_text)
        arr_message.append(str(answer.message_id))
        await self.execute.add_arr_messages(message.from_user.id, arr_message)
        messages_from_user = await self.execute.get_delivery_address(message.from_user.id)
        head_menu_button = {'back': '◀ 👈 Назад', 'post': 'Отправить заказ 📫'}
        if messages_from_user is None:
            await self.execute.record_delivery(message.from_user.id, message.text)
            change_text_head = f"Сообщение для отправки вместе с заказом:\n{message.text}"
            await self.bot.edit_head_message(change_text_head, message.chat.id, int(head_message),
                                             self.build_keyboard(head_menu_button, 2))
        else:
            arr_messages_from_user = self.get_arr_message_user(messages_from_user)
            new_arr_message_from_user = self.add_message_user(arr_messages_from_user, message.text)
            new_string_message = self.get_arr_messages_user_for_record(new_arr_message_from_user)
            await self.execute.record_delivery(message.from_user.id, new_string_message)
            new_string = '\n'.join(new_string_message.split('/////'))
            change_text_head = f"Сообщение для отправки вместе с заказом:\n{new_string}"
            await self.bot.edit_head_message(change_text_head, message.chat.id, int(head_message),
                                             self.build_keyboard(head_menu_button, 2))

    async def choice_comment_user(self, call_back: CallbackQuery):
        arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
        head_message = arr_messages[0]
        head_menu_button = {'back': '◀ 👈 Назад', 'post': 'Отправить заказ 📫'}
        await self.execute.record_delivery(call_back.from_user.id, call_back.message.text)
        change_text_head = f"Сообщение для отправки вместе с заказом:\n{call_back.message.text}"
        await self.bot.edit_head_message(change_text_head, call_back.message.chat.id, int(head_message),
                                         self.build_keyboard(head_menu_button, 2))
        await self.delete_messages(call_back.from_user.id, head_message)

    async def save_order(self, call_back: CallbackQuery, basket: dict):
        new_book = openpyxl.Workbook()
        active_list = new_book.active
        active_list.append(('Артикул', 'Наименование', 'Количество', 'Цена'))
        current_row = []
        for key, item in basket.items():
            description = await self.execute.current_description(key)
            price = float(item[1]) / float(item[0])
            current_row.append(description[0])
            current_row.append(description[2])
            current_row.append(item[0])
            current_row.append(str(price))
            active_list.append(current_row)
            current_row = []
        active_list.sheet_view.showGridLines = False
        active_list['A1'].fill = GradientFill('linear', stop=('FBDED3', 'E89E7F'))
        active_list['B1'].fill = GradientFill('linear', stop=('FBDED3', 'E89E7F'))
        active_list['C1'].fill = GradientFill('linear', stop=('FBDED3', 'E89E7F'))
        active_list['D1'].fill = GradientFill('linear', stop=('FBDED3', 'E89E7F'))
        dims = {}
        for row in active_list.rows:
            for cell in row:
                if cell.value:
                    dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))))
        for col, value in dims.items():
            active_list.column_dimensions[col].width = value
        number_order = re.sub('\W+', '', str(datetime.datetime.now()))
        filepath = f"{os.path.dirname(__file__)}\\basket\\Заказ покупателя {call_back.message.from_user.id}№" \
                   f"{number_order}.xlsx"
        new_book.save(filepath)
        new_book.close()
        list_filepath = filepath.split()
        list_order = [number_order, 'no_message', self.assembling_basket_dict_for_order(basket),
                      '_____'.join(list_filepath), 'no_score', 'new', 'no_contact']
        return number_order, self.get_order_dict('/////'.join(list_order))

    async def record_order_base(self, call_back: CallbackQuery, order_dict: dict):
        order_for_record = self.assembling_order_dict(order_dict)
        list_order = await self.execute.get_arr_order(call_back.from_user.id)
        if len(list_order) != 0:
            new_list_order = self.add_order(list_order, order_for_record)
            await self.execute.record_order(call_back.from_user.id, new_list_order)
        else:
            await self.execute.record_order(call_back.from_user.id, order_for_record)

    def get_order_dict(self, order_string: str):
        list_order = order_string.split()
        dict_orders = {}
        dict_order = {}
        for order in list_order:
            list_data = order.split('/////')
            list_message_admin = list_data[1].split('_____')
            dict_order['id_message_admins'] = list_message_admin
            composition_order = self.get_dict_basket_for_order(list_data[2])
            dict_order['composition_order'] = composition_order
            path_order = list_data[3].split('_____')
            dict_order['path_order'] = ' '.join(path_order)
            path_score = list_data[4].split('_____')
            dict_order['path_score'] = ' '.join(path_score)
            dict_order['status_order'] = list_data[5]
            contact_delivery = list_data[6].split('_____')
            dict_order['contact_order'] = ' '.join(contact_delivery)
            dict_orders[list_data[0]] = dict_order
            dict_order = {}
        return dict_orders

    def assembling_order_dict(self, order_dict: dict):
        list_order = []
        for key, item in order_dict.items():
            id_message_admins = '_____'.join(item['id_message_admins'])
            composition_order = self.assembling_basket_dict_for_order(item['composition_order'])
            filepath = item['path_order']
            path_score = item['path_score']
            status_order = item['status_order']
            contact_order = item['contact_order'].split()
            order = f"{key}/////{id_message_admins}/////{composition_order}/////{filepath}/////{path_score}" \
                    f"/////{status_order}/////{'_____'.join(contact_order)}"
            list_order.append(order)
        return ' '.join(list_order)

    @staticmethod
    def add_order(arr_order: str, new_order: str):
        list_order = arr_order.split()
        list_order.append(new_order)
        return ' '.join(list_order)

    async def set_new_contact(self, id_user: int, type_delivery: str, kind_delivery: str, value_delivery: str):
        arr_contact = await self.execute.get_arr_contact(id_user)
        dict_contact = self.get_dict_contact(arr_contact)
        if dict_contact[type_delivery][kind_delivery][0] == 'empty':
            dict_contact[type_delivery][kind_delivery][0] = value_delivery
        else:
            if self.check_contact(dict_contact[type_delivery][kind_delivery], value_delivery):
                dict_contact[type_delivery][kind_delivery].append(value_delivery)
        return self.assembling_contact_dict(dict_contact)

    @staticmethod
    def get_dict_contact(arr_contact: str):
        dict_contact = {'pickup': {}, 'delivery': {}}
        dict_contact['pickup']['record_answer_shop'] = arr_contact.split('/////')[0].split('///')[0].split('_____')
        dict_contact['pickup']['record_answer_storage'] = arr_contact.split('/////')[0].split('///')[1].split('_____')
        dict_contact['delivery']['record_answer_moscow'] = arr_contact.split('/////')[1].split('///')[0].split('_____')
        dict_contact['delivery']['record_answer_pek'] = arr_contact.split('/////')[1].split('///')[1].split('_____')
        dict_contact['delivery']['record_answer_dl'] = arr_contact.split('/////')[1].split('///')[2].split('_____')
        dict_contact['delivery']['record_answer_mt'] = arr_contact.split('/////')[1].split('///')[3].split('_____')
        dict_contact['delivery']['record_answer_cdek'] = arr_contact.split('/////')[1].split('///')[4].split('_____')
        return dict_contact

    @staticmethod
    def assembling_contact_dict(contact_dict: dict):
        contact = f"{'_____'.join(contact_dict['pickup']['record_answer_shop'])}///" \
                  f"{'_____'.join(contact_dict['pickup']['record_answer_storage'])}/////" \
                  f"{'_____'.join(contact_dict['delivery']['record_answer_moscow'])}///" \
                  f"{'_____'.join(contact_dict['delivery']['record_answer_pek'])}///" \
                  f"{'_____'.join(contact_dict['delivery']['record_answer_dl'])}///" \
                  f"{'_____'.join(contact_dict['delivery']['record_answer_mt'])}///" \
                  f"{'_____'.join(contact_dict['delivery']['record_answer_cdek'])}"
        return contact

    @staticmethod
    def check_contact(arr_contact: list, contact: str):
        check = True
        for item in arr_contact:
            if item == contact:
                check = False
                break
            else:
                check = True
        return check

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def answer_text(self, message: Message, text: str):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML,
                                    reply_to_message_id=message.message_id)

    async def edit_caption(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_caption(caption=self.format_text(text), parse_mode=ParseMode.HTML,
                                          reply_markup=keyboard)

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
            print(error)
            media_group = MediaGroupBuilder(caption=text)
            arr_photo = ["https://www.rossvik.moscow/images/no_foto.png"]
            for item in arr_photo:
                media_group.add_photo(media=item, parse_mode=ParseMode.HTML)
            return await self.bot.send_media_group(chat_id=message.chat.id, media=media_group.build())

    async def create_price_edit_caption(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.edit_caption(call_back.message,
                                         self.format_text("Каталог товаров ROSSVIK 📖"),
                                         self.build_keyboard(self.data.get_prices, 1, menu_button))
        return answer

    async def create_keyboard_edit_caption(self, call_back: CallbackQuery, list_category: list, id_category: str):
        menu_button = {'back': '◀ 👈 Назад'}
        text = await self.execute.text_category(id_category)
        await self.edit_caption(call_back.message, text,
                                self.build_keyboard(self.assembling_category_dict(list_category), 1, menu_button))

    async def create_keyboard_push_photo(self, call_back: CallbackQuery, list_category: list, id_category: str):
        menu_button = {'back': '◀ 👈 Назад'}
        text = await self.execute.text_category(id_category)
        answer = await self.bot.push_photo(call_back.message.chat.id,
                                           self.format_text(text),
                                           self.build_keyboard(self.assembling_category_dict(list_category),
                                                               1, menu_button))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    @staticmethod
    def assembling_category_dict(list_category: list):
        dict_category = {}
        for item in sorted(list_category, key=itemgetter(2), reverse=False):
            dict_category[item[0]] = item[1]
        return dict_category

    async def delete_messages(self, user_id: int, except_id_message: int = None, individual: bool = False):
        if individual:
            arr_messages = await self.execute.get_arr_messages(user_id, except_id_message)
            await self.bot.delete_messages_chat(user_id, [except_id_message])
            await self.execute.record_message(user_id, ' '.join(arr_messages))
        else:
            if except_id_message:
                arr_messages = await self.execute.get_arr_messages(user_id, except_id_message)
                if arr_messages is None:
                    pass
                elif len(arr_messages) > 0:
                    await self.bot.delete_messages_chat(user_id, arr_messages)
                    await self.execute.record_message(user_id, str(except_id_message))
                else:
                    pass
            else:
                arr_messages = await self.execute.get_arr_messages(user_id, except_id_message)
                await self.bot.delete_messages_chat(user_id, arr_messages)
                await self.execute.record_message(user_id, '')

    def build_keyboard(self, dict_button: dict, column: int, dict_return_button=None):
        keyboard = self.build_menu(self.get_list_keyboard_button(dict_button), column,
                                   footer_buttons=self.get_list_keyboard_button(dict_return_button))
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    async def edit_keyboard(message: Message, keyboard: InlineKeyboardMarkup):
        return await message.edit_reply_markup(reply_markup=keyboard)

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
    def get_arr_message_user(messages_user: str):
        arr_arr_message_user = messages_user.split('/////')
        return arr_arr_message_user

    @staticmethod
    def get_arr_messages_user_for_record(arr_messages: list):
        string_record = '/////'.join(arr_messages)
        return string_record

    @staticmethod
    def add_message_user(arr_messages: list, message: str):
        arr_messages.append(message)
        return arr_messages

    @staticmethod
    def get_list_keyboard_button(dict_button: dict):
        button_list = []
        if dict_button:
            for key, value in dict_button.items():
                if 'https://' in key:
                    button_list.append(InlineKeyboardButton(text=value, url=key))
                else:
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
