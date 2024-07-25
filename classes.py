import asyncio
import logging
import re
import os
import datetime
import openpyxl
import requests
import phonenumbers
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
from number_parser import parse
from nltk.stem import SnowballStemmer
from validate_email import validate_email
from check import is_valid

logging.basicConfig(level=logging.INFO)
snowball = SnowballStemmer(language="russian")


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
        self.catalog_logo = FSInputFile(os.path.join(os.path.split(os.path.dirname(__file__))[0],
                                                     os.environ["CATALOG_PNG"]))
        self.basket_logo = FSInputFile(os.path.join(os.path.split(os.path.dirname(__file__))[0],
                                                    os.environ["BASKET_PNG"]))
        self.order_logo = FSInputFile(os.path.join(os.path.split(os.path.dirname(__file__))[0],
                                                   os.environ["ORDER_PNG"]))
        self.search_logo = FSInputFile(os.path.join(os.path.split(os.path.dirname(__file__))[0],
                                                    os.environ["SEARCH_PNG"]))
        self.help_logo = FSInputFile(os.path.join(os.path.split(os.path.dirname(__file__))[0],
                                                  os.environ["HELP_PNG"]))

    async def delete_messages_chat(self, chat_id: int, list_message: list):
        try:
            await self.delete_messages(chat_id=chat_id, message_ids=list_message)
        except TelegramBadRequest:
            print(f'Не удалось удалить сообщения {list_message} у пользователя {chat_id}')

    async def alert_message(self, id_call_back: str, text: str):
        await self.answer_callback_query(id_call_back, text=text, show_alert=True)

    async def edit_head_message(self, text_message: str, chat_message: int, id_message: int,
                                keyboard: InlineKeyboardMarkup):
        return await self.edit_message_text(text=self.format_text(text_message), chat_id=chat_message,
                                            message_id=id_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_head_message_by_basket(self, text_message: str, chat_message: int, id_message: int,
                                          keyboard: InlineKeyboardMarkup):
        return await self.edit_message_text(text=text_message, chat_id=chat_message,
                                            message_id=id_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_head_caption_by_basket(self, text_message: str, chat_message: int, id_message: int,
                                          keyboard: InlineKeyboardMarkup):
        return await self.edit_message_caption(caption=text_message, chat_id=chat_message,
                                               message_id=id_message, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_head_keyboard(self, chat_message: int, id_message: int, keyboard: InlineKeyboardMarkup):
        return await self.edit_message_reply_markup(chat_id=chat_message, message_id=id_message, reply_markup=keyboard)

    async def hide_dealer_caption(self, text_caption: str, chat_message: int, id_message: int):
        await self.edit_message_caption(caption=text_caption, chat_id=chat_message, message_id=id_message,
                                        parse_mode=ParseMode.HTML)

    async def show_dealer_caption(self, text_caption: str, chat_message: int, id_message: int):
        await self.edit_message_caption(caption=text_caption, chat_id=chat_message, message_id=id_message,
                                        parse_mode=ParseMode.HTML)

    async def send_message_start(self, chat_id: int, keyboard: InlineKeyboardMarkup):
        return await self.send_message(chat_id=chat_id, text=self.format_text("Выберете, что Вас интересует"),
                                       parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def send_message_order(self, chat_id: int, user: str, order: str, contact: str, number_order: str,
                                 keyboard: InlineKeyboardMarkup):
        return await self.send_document(chat_id=chat_id, document=FSInputFile(order),
                                        caption=f"От клиента {user} получен новый заказ №{number_order}! {contact}",
                                        parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def push_photo(self, message_chat_id: int, text: str, keyboard: InlineKeyboardMarkup,
                         name_photo: FSInputFile):
        return await self.send_photo(chat_id=message_chat_id, photo=name_photo, caption=text,
                                     parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def save_audio(self, message: Message):
        id_file = re.sub('\W+', '', str(datetime.datetime.now()))
        name_file = f"audio_{id_file}"
        filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], f'data/document/{name_file}.mp3')
        file_id = message.audio.file_id
        caption = message.caption
        file = await self.get_file(file_id)
        await self.download_file(file_path=file.file_path, destination=f"{filepath}")
        return filepath, caption

    async def save_document(self, message: Message):
        id_file = re.sub('\W+', '', str(datetime.datetime.now()))
        name_file = f"{id_file}_{message.document.file_name}"
        filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], f'data/document/{name_file}')
        file_id = message.document.file_id
        caption = message.caption
        file = await self.get_file(file_id)
        await self.download_file(file_path=file.file_path, destination=f"{filepath}")
        return filepath, caption

    async def save_voice(self, message: Message):
        id_file = re.sub('\W+', '', str(datetime.datetime.now()))
        name_file = f"voice_{id_file}"
        filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], f'data/document/{name_file}.ogg')
        file_id = message.voice.file_id
        caption = message.caption
        file = await self.get_file(file_id)
        await self.download_file(file_path=file.file_path, destination=f"{filepath}")
        return filepath, caption

    async def save_photo(self, message: Message):
        id_file = re.sub('\W+', '', str(datetime.datetime.now()))
        name_file = f"photo_{id_file}"
        filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], f'data/document/{name_file}.jpg')
        file_id = message.photo[-1].file_id
        caption = message.caption
        file = await self.get_file(file_id)
        await self.download_file(file_path=file.file_path, destination=f"{filepath}")
        return filepath, caption

    async def save_video(self, message: Message):
        id_file = re.sub('\W+', '', str(datetime.datetime.now()))
        name_file = f"video_{id_file}"
        filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], f'data/document/{name_file}.mp4')
        file_id = message.video.file_id
        caption = message.caption
        file = await self.get_file(file_id)
        await self.download_file(file_path=file.file_path, destination=f"{filepath}")
        return filepath, caption

    @staticmethod
    def format_text(text_message: str):
        cleaner = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        clean_text = re.sub(cleaner, '', text_message)
        return f'<b>{clean_text}</b>'


class DispatcherMessage(Dispatcher):
    def __init__(self, parent, **kw):
        Dispatcher.__init__(self, **kw)
        self.timer = TimerClean(self, 82800)
        self.queues = QueuesMedia(self)
        self.queues_message = QueuesMessage()
        self.bot = parent
        self.data = DATA()
        self.execute = self.data.execute
        self.arr_auth_user = asyncio.run(self.execute.auth_user)
        self.first_keyboard = self.data.get_first_keyboard
        self.category = self.data.get_category
        self.nomenclatures = self.data.get_nomenclature
        self.pages = self.data.get_pages
        self.pages_search = self.data.get_pages_search
        self.pages_basket = self.data.get_pages_basket
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
        self.dict_hide_dealer = self.data.get_dealer_price_remove
        self.dict_show_dealer = self.data.get_dealer_price_show

        @self.message(Command("help"))
        async def cmd_help(message: Message):
            task = asyncio.create_task(self.task_command_help(message))
            task.set_name(f'{message.from_user.id}_task_command_help')
            await self.queues_message.start(task)
            await self.timer.start(message.from_user.id)

        @self.message(Command("start"))
        async def cmd_start(message: Message):
            task = asyncio.create_task(self.task_command_start(message))
            task.set_name(f'{message.from_user.id}_task_command_start')
            await self.queues_message.start(task)
            await self.timer.start(message.from_user.id)

        @self.message(Command("catalog"))
        async def cmd_catalog(message: Message):
            task = asyncio.create_task(self.task_command_catalog(message))
            task.set_name(f'{message.from_user.id}_task_command_catalog')
            await self.queues_message.start(task)
            await self.timer.start(message.from_user.id)

        @self.message(Command("news"))
        async def cmd_news(message: Message):
            task = asyncio.create_task(self.task_command_link(message))
            task.set_name(f'{message.from_user.id}_task_command_link')
            await self.queues_message.start(task)
            await self.timer.start(message.from_user.id)

        @self.message(Command("basket"))
        async def cmd_basket(message: Message):
            task = asyncio.create_task(self.task_command_basket(message))
            task.set_name(f'{message.from_user.id}_task_command_basket')
            await self.queues_message.start(task)
            await self.timer.start(message.from_user.id)

        @self.message(Command("order"))
        async def cmd_order(message: Message):
            await self.checking_bot(message)
            await self.timer.start(message.from_user.id)

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
                        task = asyncio.create_task(self.task_content_type_text(message))
                        task.set_name(f'{message.from_user.id}_task_content_type_text')
                        await self.queues_message.start(task)
                        await self.timer.start(message.from_user.id)
                    except IndexError:
                        task = asyncio.create_task(self.task_send_search_result(message))
                        task.set_name(f'{message.from_user.id}_task_send_search_result')
                        await self.queues_message.start(task)
                        await self.timer.start(message.from_user.id)
                elif message.content_type == "audio":
                    task = asyncio.create_task(self.get_audio(message))
                    await self.queues.start(message.from_user.id, task)
                    await self.timer.start(message.from_user.id)
                elif message.content_type == "document":
                    task = asyncio.create_task(self.get_document(message))
                    await self.queues.start(message.from_user.id, task)
                    await self.timer.start(message.from_user.id)
                elif message.content_type == "photo":
                    task = asyncio.create_task(self.get_photo(message))
                    await self.queues.start(message.from_user.id, task)
                    await self.timer.start(message.from_user.id)
                elif message.content_type == "sticker":
                    await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
                    print("sticker")
                elif message.content_type == "video":
                    task = asyncio.create_task(self.get_video(message))
                    await self.queues.start(message.from_user.id, task)
                    await self.timer.start(message.from_user.id)
                elif message.content_type == "video_note":
                    await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
                    print("video_note")
                elif message.content_type == "voice":
                    task = asyncio.create_task(self.get_voice(message))
                    await self.queues.start(message.from_user.id, task)
                    await self.timer.start(message.from_user.id)
                elif message.content_type == "location":
                    await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
                    print("location")
                elif message.content_type == "contact":
                    await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
                    print("contact")
                else:
                    await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            elif current_history == 'private_person':
                task = asyncio.create_task(self.task_record_name(message))
                task.set_name(f'{message.from_user.id}_task_record_name')
                await self.queues_message.start(task)
                await self.timer.start(message.from_user.id)
            elif current_history == 'individual_entrepreneur':
                task = asyncio.create_task(self.task_record_inn(message))
                task.set_name(f'{message.from_user.id}_task_record_inn')
                await self.queues_message.start(task)
                await self.timer.start(message.from_user.id)
            elif current_history == 'forward_name_company':
                task = asyncio.create_task(self.task_record_name_company(message))
                task.set_name(f'{message.from_user.id}_task_record_name_company')
                await self.queues_message.start(task)
                await self.timer.start(message.from_user.id)
            elif current_history == 'forward_email':
                task = asyncio.create_task(self.task_record_email(message))
                task.set_name(f'{message.from_user.id}_task_record_email')
                await self.queues_message.start(task)
                await self.timer.start(message.from_user.id)
            elif current_history == 'forward_telephone':
                task = asyncio.create_task(self.task_record_telephone(message))
                task.set_name(f'{message.from_user.id}task_record_telephone')
                await self.queues_message.start(task)
                await self.timer.start(message.from_user.id)
            elif current_history == 'individual_entrepreneur':
                print('Индивидуальный предприниматель')
                await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            elif current_history == 'limited_liability_company':
                print('ООО')
                await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            else:
                if message.content_type == "text" or message.content_type == "voice":
                    task = asyncio.create_task(self.task_send_search_result(message))
                    task.set_name(f'{message.from_user.id}_task_send_search_result')
                    await self.queues_message.start(task)
                    await self.timer.start(message.from_user.id)
                else:
                    await self.bot.delete_messages_chat(message.chat.id, [message.message_id])

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'catalog'))
        async def send_catalog_message(callback: CallbackQuery):
            task = asyncio.create_task(self.task_catalog(callback))
            task.set_name(f'{callback.from_user.id}_task_catalog')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_hide_dealer)))
        async def remove_dealer_price(callback: CallbackQuery):
            task = asyncio.create_task(self.remove_price(callback))
            task.set_name(f'{callback.from_user.id}_remove_price')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_show_dealer)))
        async def show_dealer_price(callback: CallbackQuery):
            task = asyncio.create_task(self.show_price(callback))
            task.set_name(f'{callback.from_user.id}_show_price')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.category)))
        async def send_next_category(callback: CallbackQuery):
            task = asyncio.create_task(self.task_next_category(callback))
            task.set_name(f'{callback.from_user.id}_task_next_category')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages)))
        async def send_next_page(callback: CallbackQuery):
            task = asyncio.create_task(self.task_next_page(callback))
            task.set_name(f'{callback.from_user.id}_task_next_page')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages_search)))
        async def send_next_page_search(callback: CallbackQuery):
            task = asyncio.create_task(self.task_next_page_search(callback))
            task.set_name(f'{callback.from_user.id}_task_next_page_search')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.nomenclatures)))
        async def send_description(callback: CallbackQuery):
            task = asyncio.create_task(self.task_description(callback))
            task.set_name(f'{callback.from_user.id}_task_description')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_add)))
        async def send_add(callback: CallbackQuery):
            task = asyncio.create_task(self.add_nomenclature(callback))
            task.set_name(f'{callback.from_user.id}_add_nomenclature')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_back_add)))
        async def send_back_add(callback: CallbackQuery):
            task = asyncio.create_task(self.back_add_nomenclature(callback))
            task.set_name(f'{callback.from_user.id}_back_add_nomenclature')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_button_calculater)))
        async def send_change_amount(callback: CallbackQuery):
            task = asyncio.create_task(self.change_amount(callback))
            task.set_name(f'{callback.from_user.id}_change_amount')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_minus)))
        async def send_change_minus(callback: CallbackQuery):
            task = asyncio.create_task(self.minus_amount(callback))
            task.set_name(f'{callback.from_user.id}_minus_amount')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_plus)))
        async def send_change_plus(callback: CallbackQuery):
            task = asyncio.create_task(self.plus_amount(callback))
            task.set_name(f'{callback.from_user.id}_plus_amount')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_delete)))
        async def send_change_delete(callback: CallbackQuery):
            task = asyncio.create_task(self.delete_amount(callback))
            task.set_name(f'{callback.from_user.id}_delete_amount')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.dict_done)))
        async def send_done_basket(callback: CallbackQuery):
            task = asyncio.create_task(self.add_to_basket(callback))
            task.set_name(f'{callback.from_user.id}_add_to_basket')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'basket'))
        async def send_show_basket(callback: CallbackQuery):
            task = asyncio.create_task(self.task_show_basket(callback))
            task.set_name(f'{callback.from_user.id}_task_show_basket')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.pages_basket)))
        async def send_next_page_basket(callback: CallbackQuery):
            task = asyncio.create_task(self.task_next_page_basket(callback))
            task.set_name(f'{callback.from_user.id}_task_next_page_basket')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.button_basket_minus)))
        async def send_basket_minus(callback: CallbackQuery):
            task = asyncio.create_task(self.task_basket_minus(callback))
            task.set_name(f'{callback.from_user.id}_task_basket_minus')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.button_basket_plus)))
        async def send_basket_plus(callback: CallbackQuery):
            task = asyncio.create_task(self.task_basket_plus(callback))
            task.set_name(f'{callback.from_user.id}_task_basket_plus')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'clean'))
        async def send_clean_basket(callback: CallbackQuery):
            task = asyncio.create_task(self.task_clean_basket(callback))
            task.set_name(f'{callback.from_user.id}_task_clean_basket')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'post'))
        async def post_order(callback: CallbackQuery):
            task = asyncio.create_task(self.task_post_admin(callback))
            task.set_name(f'{callback.from_user.id}_task_post_admin')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'choice_delivery'))
        async def send_choice_delivery(callback: CallbackQuery):
            task = asyncio.create_task(self.task_choice_delivery_user(callback))
            task.set_name(f'{callback.from_user.id}_task_choice_delivery_user')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.choice_delivery)))
        async def send_pickup_delivery(callback: CallbackQuery):
            task = asyncio.create_task(self.task_pickup_or_delivery(callback))
            task.set_name(f'{callback.from_user.id}_task_pickup_or_delivery')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.kind_pickup)))
        async def send_kind_pickup(callback: CallbackQuery):
            task = asyncio.create_task(self.task_record_answer_pickup(callback))
            task.set_name(f'{callback.from_user.id}_task_record_answer_pickup')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.in_(self.kind_delivery)))
        async def send_kind_delivery(callback: CallbackQuery):
            task = asyncio.create_task(self.task_record_answer_delivery(callback))
            task.set_name(f'{callback.from_user.id}_task_record_answer_delivery')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'new_attachments'))
        async def send_attachments(callback: CallbackQuery):
            task = asyncio.create_task(self.task_show_new_attachments(callback))
            task.set_name(f'{callback.from_user.id}_task_show_new_attachments')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.contains('nested')))
        async def send_nested(callback: CallbackQuery):
            task = asyncio.create_task(self.task_show_nested(callback))
            task.set_name(f'{callback.from_user.id}_task_show_nested')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.contains('choice_contact')))
        async def send_choice_contact(callback: CallbackQuery):
            task = asyncio.create_task(self.task_choice_comment_user(callback))
            task.set_name(f'{callback.from_user.id}_task_choice_comment_user')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data.contains('delete_record')))
        async def send_delete_contact(callback: CallbackQuery):
            task = asyncio.create_task(self.delete_record_user(callback))
            task.set_name(f'{callback.from_user.id}_delete_record_user')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'fill_details'))
        async def send_fill_details(callback: CallbackQuery):
            task = asyncio.create_task(self.task_fill_details(callback))
            task.set_name(f'{callback.from_user.id}_task_fill_details')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'private_person'))
        async def send_private_person(callback: CallbackQuery):
            task = asyncio.create_task(self.task_private_person(callback))
            task.set_name(f'{callback.from_user.id}_task_private_person')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'individual_entrepreneur'))
        async def send_individual_entrepreneur(callback: CallbackQuery):
            task = asyncio.create_task(self.task_individual_entrepreneur(callback))
            task.set_name(f'{callback.from_user.id}_task_individual_entrepreneur')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'forward_name_company'))
        async def send_forward_name_company(callback: CallbackQuery):
            task = asyncio.create_task(self.task_forward_name_company(callback))
            task.set_name(f'{callback.from_user.id}_task_forward_name_company')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'forward_email'))
        async def send_forward_email(callback: CallbackQuery):
            task = asyncio.create_task(self.task_forward_email(callback))
            task.set_name(f'{callback.from_user.id}_task_forward_email')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'forward_telephone'))
        async def send_forward_telephone(callback: CallbackQuery):
            task = asyncio.create_task(self.task_forward_telephone(callback))
            task.set_name(f'{callback.from_user.id}_task_forward_telephone')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'forward_done'))
        async def send_forward_done(callback: CallbackQuery):
            task = asyncio.create_task(self.task_forward_done(callback))
            task.set_name(f'{callback.from_user.id}_task_forward_done')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

        @self.callback_query(F.from_user.id.in_(self.arr_auth_user) & (F.data == 'back'))
        async def send_return_message(callback: CallbackQuery):
            task = asyncio.create_task(self.task_back(callback))
            task.set_name(f'{callback.from_user.id}_task_back')
            await self.queues_message.start(task)
            await self.timer.start(callback.from_user.id)

    async def task_back(self, call_back: CallbackQuery):
        current = await self.execute.delete_element_history(call_back.from_user.id, 1)
        if 'search' in current:
            current = await self.execute.delete_element_history(call_back.from_user.id, 1)
        if current == '/start':
            await self.return_start(call_back)
        elif current == 'catalog':
            await self.catalog(call_back)
        elif current == 'help':
            await self.return_help_message(call_back)
        elif current == 'news':
            await self.return_show_link(call_back)
        elif current in self.category:
            await self.return_category(call_back, current)
        elif current in self.pages:
            await self.return_page(call_back, current)
            await self.execute.add_element_history(call_back.from_user.id, current)
        elif current in self.nomenclatures:
            await self.description(call_back, current)
        elif current in self.pages_search:
            previous_history = await self.execute.delete_element_history(call_back.from_user.id, 1)
            result_search = await self.search(self.get_text_for_search(previous_history.split('___')[1]))
            await self.return_page_search(call_back, result_search, current)
            await self.execute.add_element_history(call_back.from_user.id, current)
        elif current in self.pages_basket:
            await self.show_basket(call_back, current)
        elif current == 'choice_delivery':
            await self.choice_delivery_user(call_back)
        elif current in self.choice_delivery:
            if current == 'pickup':
                await self.pickup(call_back)
            elif current == 'delivery':
                await self.delivery(call_back)
        elif current in self.kind_pickup:
            await self.record_answer_pickup(call_back, current)
        elif current in self.kind_delivery:
            await self.record_answer_delivery(call_back, current)
        elif 'nested' in current:
            await self.show_nested(call_back, current)
        elif current == 'fill_details':
            await self.fill_details(call_back)
        elif current == 'private_person':
            await self.private_person(call_back)
        elif current == 'individual_entrepreneur':
            await self.individual_entrepreneur(call_back)
        elif current == 'forward_name_company':
            await self.forward_name_company(call_back)
        elif current == 'forward_email':
            await self.forward_email(call_back)
        elif current == 'forward_telephone':
            await self.forward_telephone(call_back)
        return True

    async def checking_bot(self, message: Message):
        if message.from_user.is_bot:
            await self.bot.restrict_chat_member(message.chat.id, message.from_user.id, ChatPermissions())

    async def task_command_help(self, message: Message):
        await self.checking_bot(message)
        if await self.execute.start_message(message):
            await self.execute.restart_catalog(message, '/start')
        else:
            await self.execute.start_record_new_user(message)
            self.arr_auth_user[message.from_user.id] = None
        await self.help_message(message)
        await self.execute.add_element_history(message.from_user.id, 'help')
        return True

    async def help_message(self, message: Message):
        whitespace = '\n'
        first_keyboard = await self.data.get_first_keyboard(message.from_user.id)
        answer = await self.bot.push_photo(message.chat.id,
                                           self.format_text(f"Вы можете воспользоваться быстрой навигацией,"
                                                            f"отправляя следующие команды:{whitespace}{whitespace}"
                                                            f"/start - главное меню{whitespace}"
                                                            f"/catalog - каталог товара{whitespace}"
                                                            f"/news - новости{whitespace}"
                                                            f"/basket - корзина{whitespace}"
                                                            f"/order - история заказов{whitespace}{whitespace}"
                                                            f"Поиск товара:{whitespace}{whitespace}"
                                                            f"При отправке боту сообщения происходит "
                                                            f"поиск товара в каталоге "
                                                            f"по содержимому сообщения, разделенному пробелами. Можно "
                                                            f"указывать не только слова, но и символы, "
                                                            f"которые содержатся, например, в наименовании товара."
                                                            f"{whitespace}Чтобы понять, "
                                                            f"как это работает, попробуйте отправить боту "
                                                            f"сообщение:{whitespace}пласт вст{whitespace}{whitespace}"
                                                            f"УВЕДОМЛЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ: "
                                                            f"Все данные, полученные в процессе взаимодействия между "
                                                            f"Ботом и Пользователем: фото, видео, текстовая "
                                                            f"информация, а также любые отправленные документы, "
                                                            f"которые содержат конфиденциальную информацию не "
                                                            f"подлежат использованию, копированию, распространению, "
                                                            f"а также осуществлению любых других действий "
                                                            f"на основе этой информации."),
                                           self.build_keyboard(first_keyboard, 1), self.bot.help_logo)
        await self.execute.add_element_message(message.from_user.id, message.message_id)
        await self.delete_messages(message.from_user.id)
        await self.execute.add_element_message(message.from_user.id, answer.message_id)

    async def return_help_message(self, call_back: CallbackQuery):
        whitespace = '\n'
        first_keyboard = await self.data.get_first_keyboard(call_back.from_user.id)
        answer = await self.bot.push_photo(call_back.message.chat.id,
                                           self.format_text(f"Вы можете воспользоваться быстрой навигацией,"
                                                            f"отправляя следующие команды:{whitespace}{whitespace}"
                                                            f"/start - главное меню{whitespace}"
                                                            f"/catalog - каталог товара{whitespace}"
                                                            f"/news - новости{whitespace}"
                                                            f"/basket - корзина{whitespace}"
                                                            f"/order - история заказов{whitespace}{whitespace}"
                                                            f"Поиск товара:{whitespace}{whitespace}"
                                                            f"При отправке боту сообщения происходит "
                                                            f"поиск товара в каталоге "
                                                            f"по содержимому сообщения, разделенному пробелами. Можно "
                                                            f"указывать не только слова, но и символы, "
                                                            f"которые содержатся, например, в наименовании товара."
                                                            f"{whitespace}Чтобы понять, "
                                                            f"как это работает, попробуйте отправить боту "
                                                            f"сообщение:{whitespace}пласт вст{whitespace}{whitespace}"
                                                            f"УВЕДОМЛЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ: "
                                                            f"Все данные, полученные в процессе взаимодействия между "
                                                            f"Ботом и Пользователем: фото, видео, текстовая "
                                                            f"информация, а также любые отправленные документы, "
                                                            f"которые содержат конфиденциальную информацию не "
                                                            f"подлежат использованию, копированию, распространению, "
                                                            f"а также осуществлению любых других действий "
                                                            f"на основе этой информации."),
                                           self.build_keyboard(first_keyboard, 1), self.bot.help_logo)
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def task_command_start(self, message: Message):
        await self.checking_bot(message)
        first_keyboard = await self.data.get_first_keyboard(message.from_user.id)
        answer = await self.answer_message(message, "Выберете, что Вас интересует ⤵ ⤵ ⤵",
                                           self.build_keyboard(first_keyboard, 1))
        if await self.execute.start_message(message):
            await self.execute.restart_catalog(message, '/start')
            await self.execute.add_element_message(message.from_user.id, message.message_id)
        else:
            await self.execute.start_record_new_user(message)
            self.arr_auth_user[message.from_user.id] = None
        await self.delete_messages(message.from_user.id)
        await self.execute.add_element_message(message.from_user.id, answer.message_id)
        return True

    async def return_start(self, call_back: CallbackQuery):
        first_keyboard = await self.data.get_first_keyboard(call_back.from_user.id)
        answer = await self.answer_message(call_back.message, "Выберете, что Вас интересует ⤵ ⤵ ⤵",
                                           self.build_keyboard(first_keyboard, 1))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def start_for_timer(self, user_id: int):
        first_keyboard = await self.data.get_first_keyboard(user_id)
        answer = await self.bot.send_message_start(user_id, self.build_keyboard(first_keyboard, 1))
        await self.execute.add_element_message(user_id, answer.message_id)

    async def task_command_catalog(self, message: Message):
        await self.checking_bot(message)
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.bot.push_photo(message.chat.id, self.format_text("Каталог товаров 📖"),
                                           self.build_keyboard(self.data.get_prices, 1, menu_button),
                                           self.bot.catalog_logo)
        await self.execute.add_element_message(message.from_user.id, message.message_id)
        await self.delete_messages(message.from_user.id)
        await self.execute.add_element_message(message.from_user.id, answer.message_id)
        await self.execute.restart_catalog(message, '/start catalog')
        return True

    async def task_catalog(self, call_back: CallbackQuery):
        await self.catalog(call_back)
        await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def catalog(self, call_back: CallbackQuery):
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.bot.push_photo(call_back.message.chat.id, self.format_text("Каталог товаров 📖"),
                                           self.build_keyboard(self.data.get_prices, 1, menu_button),
                                           self.bot.catalog_logo)
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_element_message(call_back.from_user.id, answer.message_id)

    async def task_command_link(self, message: Message):
        await self.checking_bot(message)
        await self.show_link(message)
        await self.execute.add_element_history(message.from_user.id, 'news')
        return True

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

    async def task_next_category(self, call_back: CallbackQuery):
        if await self.next_category(call_back):
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        else:
            await self.execute.add_element_history(call_back.from_user.id, f"{call_back.data} Стр.1")
        return True

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
            await self.create_keyboard_push_photo(call_back, current_category, current_history, self.bot.catalog_logo)
        else:
            new_current = await self.execute.delete_element_history(call_back.from_user.id, 1)
            if new_current == 'catalog':
                await self.catalog(call_back)
            else:
                current_category = await self.execute.current_category(new_current)
                await self.create_keyboard_push_photo(call_back, current_category, new_current, self.bot.catalog_logo)

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
            if value[1]:
                photo = value[1].split()[0]
            else:
                photo = "https://www.rossvik.moscow/images/no_foto.png"
            answer = await self.answer_photo(heading, photo, value[0], self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

    async def task_description(self, call_back: CallbackQuery):
        await self.description(call_back, call_back.data)
        await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def description(self, call_back: CallbackQuery, id_nomenclature: str):
        current_description = await self.description_nomenclature(id_nomenclature, call_back.from_user.id,
                                                                  call_back.id)
        arr_answer = await self.send_photo(call_back.message, current_description[0], current_description[1], 10)
        basket = await self.data.get_basket(call_back.from_user.id)
        menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️', 'basket': basket['basket']}
        if current_description[3]:
            answer_description = await self.answer_message(arr_answer[0], current_description[2],
                                                           self.build_keyboard(menu_button, 2, current_description[3]))
        else:
            answer_description = await self.answer_message(arr_answer[0], current_description[2],
                                                           self.build_keyboard(menu_button, 2))
        arr_answer.append(answer_description)
        arr_message = []
        for item_message in arr_answer:
            arr_message.append(str(item_message.message_id))
        await self.delete_messages(call_back.from_user.id)
        await self.execute.add_arr_messages(call_back.from_user.id, arr_message)

    async def remove_price(self, call_back: CallbackQuery):
        id_nomenclature = call_back.data.split('remove_dealer_price')[0]
        current_description = await self.description_nomenclature(id_nomenclature, call_back.from_user.id,
                                                                  call_back.id)
        arr_text = current_description[1].split('\n')
        arr_text.pop(4)
        new_text = '\n'.join(arr_text)
        basket = await self.data.get_basket(call_back.from_user.id)
        menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️', 'basket': basket['basket']}
        dict_show = {f'{id_nomenclature}show_dealer_price': '👀 Показать дилерскую цену'}
        arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
        await self.bot.hide_dealer_caption(new_text, call_back.message.chat.id, arr_messages[0])
        await self.edit_keyboard(call_back.message, self.build_keyboard(menu_button, 2, dict_show))
        return True

    async def show_price(self, call_back: CallbackQuery):
        id_nomenclature = call_back.data.split('show_dealer_price')[0]
        current_description = await self.description_nomenclature(id_nomenclature, call_back.from_user.id,
                                                                  call_back.id)
        basket = await self.data.get_basket(call_back.from_user.id)
        menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️', 'basket': basket['basket']}
        dict_hide = {f'{id_nomenclature}remove_dealer_price': '🙈 Скрыть дилерскую цену'}
        arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
        await self.bot.hide_dealer_caption(current_description[1], call_back.message.chat.id, arr_messages[0])
        await self.edit_keyboard(call_back.message, self.build_keyboard(menu_button, 2, dict_hide))
        return True

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
            dict_hide = {f'{id_item}remove_dealer_price': '🙈 Скрыть дилерскую цену'}
        else:
            info_nomenclature = f'{self.format_text(arr_description[2])}{whitespace}' \
                                f'Артикул: {self.format_text(arr_description[0])}{whitespace}' \
                                f'Бренд: {self.format_text(arr_description[1])}{whitespace}' \
                                f'Цена: {self.format_text(self.format_price(float(arr_description[8])))}{whitespace}' \
                                f'Наличие: {self.format_text(availability)}{whitespace}'
            dict_hide = None
        description_text = f'{arr_description[4]}{whitespace}' \
                           f'{arr_description[5]}'
        if re.sub('\W+', '', description_text) == "":
            description_text = "Нет подробной информации"
        return arr_description[6], info_nomenclature, description_text, dict_hide

    async def task_next_page(self, call_back: CallbackQuery):
        if await self.next_page(call_back):
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

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
                if value[1]:
                    photo = value[1].split()[0]
                else:
                    photo = "https://www.rossvik.moscow/images/no_foto.png"
                answer = await self.answer_photo(heading, photo, value[0], self.build_keyboard(menu_button, 2))
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
                                            self.build_keyboard(pages, 5), self.bot.catalog_logo)
        await self.delete_messages(call_back.from_user.id)
        await asyncio.sleep(0.5)
        arr_answers = [str(heading.message_id)]
        for key, value in current_nomenclature[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            if value[1]:
                photo = value[1].split()[0]
            else:
                photo = "https://www.rossvik.moscow/images/no_foto.png"
            answer = await self.answer_photo(heading, photo, value[0], self.build_keyboard(menu_button, 2))
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
        if call_back.message.caption:
            await self.edit_caption(call_back.message, info_nomenclature, self.build_keyboard(menu_button, 3))
        else:
            await self.edit_message(call_back.message, info_nomenclature, self.build_keyboard(menu_button, 3))
        return True

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
        if call_back.message.caption:
            await self.edit_caption(call_back.message, info_nomenclature, self.build_keyboard(menu_button, 2))
        else:
            await self.edit_message(call_back.message, info_nomenclature, self.build_keyboard(menu_button, 3))
        return True

    async def change_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        button = self.dict_button_calculater[call_back.data]
        id_nomenclature = call_back.data.split('///')[0]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        if call_back.message.caption:
            amount = self.get_amount(call_back.message.caption, button)
        else:
            amount = self.get_amount(call_back.message.text, button)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        sum_nomenclature = float(amount) * float(price)
        if call_back.message.caption:
            text = f"{call_back.message.caption.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            try:
                await self.edit_caption(call_back.message, text, self.build_keyboard(menu_button, 3))
                return True
            except TelegramBadRequest:
                return True
        else:
            text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                   f"{amount} шт. х {self.format_price(float(price))} = {self.format_price(float(sum_nomenclature))}"
            try:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
                return True
            except TelegramBadRequest:
                return True

    async def minus_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_minus[call_back.data]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        if call_back.message.caption:
            amount = self.get_amount_minus(call_back.message.caption)
        else:
            amount = self.get_amount_minus(call_back.message.text)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            if call_back.message.caption:
                text = f"{call_back.message.caption.split(whitespace)[0]}{whitespace}" \
                       f"{amount} шт. х {self.format_price(float(price))} = " \
                       f"{self.format_price(float(sum_nomenclature))}"
                try:
                    await self.edit_caption(call_back.message, text, self.build_keyboard(menu_button, 3))
                    return True
                except TelegramBadRequest:
                    return True
            else:
                text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                       f"{amount} шт. х {self.format_price(float(price))} = " \
                       f"{self.format_price(float(sum_nomenclature))}"
                try:
                    await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
                    return True
                except TelegramBadRequest:
                    return True
        else:
            return True

    async def plus_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_plus[call_back.data]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        if call_back.message.caption:
            amount = self.get_amount_minus(call_back.message.caption)
        else:
            amount = self.get_amount_minus(call_back.message.text)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            if call_back.message.caption:
                text = f"{call_back.message.caption.split(whitespace)[0]}{whitespace}" \
                       f"{amount} шт. х {self.format_price(float(price))} = " \
                       f"{self.format_price(float(sum_nomenclature))}"
                try:
                    await self.edit_caption(call_back.message, text, self.build_keyboard(menu_button, 3))
                    return True
                except TelegramBadRequest:
                    return True
            else:
                text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                       f"{amount} шт. х {self.format_price(float(price))} = " \
                       f"{self.format_price(float(sum_nomenclature))}"
                try:
                    await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
                    return True
                except TelegramBadRequest:
                    return True
        else:
            return True

    async def delete_amount(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_delete[call_back.data]
        menu_button = await self.data.get_calculater(call_back.from_user.id, id_nomenclature)
        arr_description = await self.execute.current_description(id_nomenclature)
        if call_back.message.caption:
            amount = self.get_amount_delete(call_back.message.caption)
        else:
            amount = self.get_amount_delete(call_back.message.text)
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            if call_back.message.caption:
                text = f"{call_back.message.caption.split(whitespace)[0]}{whitespace}" \
                       f"{amount} шт. х {self.format_price(float(price))} = " \
                       f"{self.format_price(float(sum_nomenclature))}"
                try:
                    await self.edit_caption(call_back.message, text, self.build_keyboard(menu_button, 3))
                    return True
                except TelegramBadRequest:
                    return True
            else:
                text = f"{call_back.message.text.split(whitespace)[0]}{whitespace}" \
                       f"{amount} шт. х {self.format_price(float(price))} = " \
                       f"{self.format_price(float(sum_nomenclature))}"
                try:
                    await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 3))
                    return True
                except TelegramBadRequest:
                    return True
        else:
            return True

    async def add_to_basket(self, call_back: CallbackQuery):
        whitespace = '\n'
        id_nomenclature = self.dict_done[call_back.data]
        arr_description = await self.execute.current_description(id_nomenclature)
        if call_back.message.caption:
            amount = await self.check_amount(call_back.message.caption, call_back.id, arr_description[7])
        else:
            amount = await self.check_amount(call_back.message.text, call_back.id, arr_description[7])
        if self.arr_auth_user[call_back.from_user.id] == 'diler':
            price = self.get_dealer(arr_description[8], arr_description[9])
        else:
            price = arr_description[8]
        if amount is not None:
            sum_nomenclature = float(amount) * float(price)
            check_nomenclature_in_basket = await self.execute.current_nomenclature_basket(call_back.from_user.id,
                                                                                          id_nomenclature)
            if check_nomenclature_in_basket is None:
                await self.execute.add_basket_nomenclature(call_back.from_user.id, id_nomenclature, float(amount),
                                                           sum_nomenclature)
            else:
                new_amount = float(amount) + float(check_nomenclature_in_basket[2])
                new_sum_nomenclature = sum_nomenclature + float(check_nomenclature_in_basket[3])
                await self.execute.update_basket_nomenclature(call_back.from_user.id, id_nomenclature,
                                                              float(new_amount), new_sum_nomenclature)
            text = f"Вы добавили {arr_description[2]} в количестве:{whitespace}" \
                   f"{amount} шт. на сумму {self.format_price(float(sum_nomenclature))} в корзину."
            basket = await self.data.get_basket(call_back.from_user.id)
            current_history = await self.execute.get_element_history(call_back.from_user.id, -1)
            if current_history in self.dict_add:
                menu_button = {'back': '◀ 👈 Назад', f'{id_nomenclature}add': 'Добавить ✅🗑️'}
                await self.execute.delete_element_history(call_back.from_user.id, 1)
            else:
                menu_button = {'back': '◀ 👈 Назад', id_nomenclature: 'Подробнее 👀📸',
                               f'{id_nomenclature}add': 'Добавить ✅🗑️'}
            if call_back.message.caption:
                await self.edit_caption(call_back.message, text, self.build_keyboard(menu_button, 2,
                                                                                     {'basket': basket['basket']}))
            else:
                await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 2,
                                                                                     {'basket': basket['basket']}))
            return True
        else:
            return True

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

    async def task_command_basket(self, message: Message):
        await self.checking_bot(message)
        await self.show_basket_by_command(message, message.from_user.id)
        await self.execute.add_element_history(message.from_user.id, 'Корзина_Стр.1')
        return True

    async def task_show_basket(self, call_back: CallbackQuery):
        await self.show_basket(call_back, 'Корзина_Стр.1')
        await self.execute.add_element_history(call_back.from_user.id, 'Корзина_Стр.1')
        return True

    async def task_next_page_basket(self, call_back: CallbackQuery):
        await self.show_basket(call_back, call_back.data)
        await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def show_basket(self, call_back: CallbackQuery, number_page: str):
        if call_back.message.text and '№' in call_back.message.text and \
                self.pages_basket[number_page] == call_back.message.text.split('№')[1]:
            pass
        elif call_back.message.caption and '№' in call_back.message.caption and \
                self.pages_basket[number_page] == call_back.message.caption.split('№')[1]:
            pass
        else:
            whitespace = '\n'
            number = number_page.split('Корзина_Стр.')[1]
            number_page = f'{whitespace}Страница №{number}'
            current_basket_dict = await self.execute.current_basket(call_back.from_user.id)
            if current_basket_dict is None:
                text = 'Ваша корзина пуста 😭😔💔'
                menu_button = {'back': '◀ 👈 Назад'}
                answer = await self.bot.push_photo(call_back.message.chat.id, self.format_text(text),
                                                   self.build_keyboard(menu_button, 1), self.bot.basket_logo)
                await self.delete_messages(call_back.from_user.id)
                await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
            else:
                pages = {}
                for page in current_basket_dict.keys():
                    pages[page] = page
                sum_basket = await self.execute.current_sum_basket(call_back.from_user.id)
                text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                       f"{self.format_text(self.format_price(float(sum_basket)))}:"
                menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                               'choice_delivery': 'Оформить заказ 📧📦📲'}
                if call_back.message.caption:
                    if "Сейчас в Вашу корзину добавлены товары на общую сумму " in call_back.message.caption:
                        heading = await self.edit_caption_by_basket(call_back.message,
                                                                    text + self.format_text(number_page),
                                                                    self.build_keyboard(pages, 3, menu_button))
                        await self.delete_messages(call_back.from_user.id, heading.message_id)
                        arr_answers = []
                    else:
                        heading = await self.bot.push_photo(call_back.message.chat.id,
                                                            text + self.format_text(number_page),
                                                            self.build_keyboard(pages, 3, menu_button),
                                                            self.bot.basket_logo)
                        await self.delete_messages(call_back.from_user.id)
                        arr_answers = [str(heading.message_id)]
                else:
                    heading = await self.bot.push_photo(call_back.message.chat.id, text + self.format_text(number_page),
                                                        self.build_keyboard(pages, 3, menu_button),
                                                        self.bot.basket_logo)
                    await self.delete_messages(call_back.from_user.id)
                    arr_answers = [str(heading.message_id)]
                if f'Корзина_Стр.{number}' not in current_basket_dict.keys():
                    number = '1'
                for key, item in current_basket_dict[f'Корзина_Стр.{number}'].items():
                    name = await self.execute.current_description(key)
                    text = f"{name[2]}:{whitespace}{self.format_text(str(int(item[0])))} шт. на сумму " \
                           f"{self.format_text(self.format_price(float(item[1])))}"
                    menu_button = {f'{key}basket_minus': '➖', f'{key}basket_plus': '➕', key: 'Подробнее 👀📸'}
                    answer = await self.answer_message_by_basket(heading, text, self.build_keyboard(menu_button, 2))
                    arr_answers.append(str(answer.message_id))
                await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

    async def show_basket_by_command(self, message: Message, id_user: int):
        whitespace = '\n'
        number_page = whitespace + 'Страница №1'
        current_basket_dict = await self.execute.current_basket(id_user)
        if current_basket_dict is None:
            text = 'Ваша корзина пуста 😭😔💔'
            menu_button = {'back': '◀ 👈 Назад'}
            answer = await self.bot.push_photo(message.chat.id, self.format_text(text),
                                               self.build_keyboard(menu_button, 1), self.bot.basket_logo)
            await self.execute.add_element_message(message.from_user.id, message.message_id)
            await self.delete_messages(message.from_user.id)
            await self.execute.add_element_message(message.from_user.id, answer.message_id)
        else:
            pages = {}
            for page in current_basket_dict.keys():
                pages[page] = page
            sum_basket = await self.execute.current_sum_basket(id_user)
            text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                   f"{self.format_text(self.format_price(float(sum_basket)))}:"
            menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                           'choice_delivery': 'Оформить заказ 📧📦📲'}
            heading = await self.bot.push_photo(message.chat.id, text + self.format_text(number_page),
                                                self.build_keyboard(pages, 3, menu_button), self.bot.basket_logo)
            await self.execute.add_element_message(message.from_user.id, message.message_id)
            await self.delete_messages(message.from_user.id)
            await self.execute.add_element_message(message.from_user.id, heading.message_id)
            arr_answers = []
            for key, item in current_basket_dict['Корзина_Стр.1'].items():
                name = await self.execute.current_description(key)
                text = f"{name[2]}:{whitespace}{self.format_text(str(int(item[0])))} шт. на сумму " \
                       f"{self.format_text(self.format_price(float(item[1])))}"
                menu_button = {f'{key}basket_minus': '➖', f'{key}basket_plus': '➕', key: 'Подробнее 👀📸'}
                answer = await self.answer_message_by_basket(heading, text, self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            await self.execute.add_arr_messages(id_user, arr_answers)

    async def task_clean_basket(self, call_back: CallbackQuery):
        await self.execute.clean_basket(call_back.from_user.id)
        await self.clean_basket_message(call_back)
        return True

    async def clean_basket_message(self, call_back: CallbackQuery):
        text = 'Ваша корзина пуста 😭😔💔'
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.edit_caption(call_back.message, text, self.build_keyboard(menu_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)
        await self.delete_history_basket(call_back.from_user.id, 'Корзина')

    async def task_basket_minus(self, call_back: CallbackQuery):
        current_page_basket = await self.execute.get_element_history(call_back.from_user.id, -1)
        new_page_basket = await self.minus_amount_basket(call_back, current_page_basket)
        if new_page_basket != current_page_basket:
            await self.execute.delete_element_history(call_back.from_user.id, 1)
            await self.execute.add_element_history(call_back.from_user.id, new_page_basket)
        return True

    async def minus_amount_basket(self, call_back: CallbackQuery, number_page: str):
        try:
            whitespace = '\n'
            number = number_page.split('Корзина_Стр.')[1]
            number_page_basket = f'{whitespace}Страница №{number}'
            current_nomenclature = await self.execute.current_nomenclature_basket(call_back.from_user.id,
                                                                                  self.button_basket_minus[
                                                                                      call_back.data])
            current_amount = current_nomenclature[2]
            current_sum = current_nomenclature[3]
            price = float(current_sum / current_amount)
            if current_amount > 1:
                new_amount = current_amount - 1
                new_sum = new_amount * price
                await self.execute.update_basket_nomenclature(call_back.from_user.id,
                                                              self.button_basket_minus[call_back.data],
                                                              new_amount,
                                                              new_sum)
                name = await self.execute.current_description(self.button_basket_minus[call_back.data])
                text = f"{name[2]}:{whitespace}{self.format_text(str(int(new_amount)))} шт. на сумму " \
                       f"{self.format_text(self.format_price(float(new_sum)))}"
                menu_button = {f'{self.button_basket_minus[call_back.data]}basket_minus': '➖',
                               f'{self.button_basket_minus[call_back.data]}basket_plus': '➕',
                               self.button_basket_minus[call_back.data]: 'Подробнее 👀📸'}
                await self.edit_message_by_basket(call_back.message, text,  self.build_keyboard(menu_button, 2))
                current_basket_dict = await self.execute.current_basket(call_back.from_user.id)
                pages = {}
                for page in current_basket_dict.keys():
                    pages[page] = page
                sum_basket = await self.execute.current_sum_basket(call_back.from_user.id)
                head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                            f"{self.format_text(self.format_price(float(sum_basket)))}:"
                head_menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                    'choice_delivery': 'Оформить заказ 📧📦📲'}
                arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
                await self.bot.edit_head_caption_by_basket(head_text + self.format_text(number_page_basket),
                                                           call_back.message.chat.id, arr_messages[0],
                                                           self.build_keyboard(pages, 3, head_menu_button))
                return number_page
            else:
                await self.execute.delete_nomenclature_basket(call_back.from_user.id,
                                                              self.button_basket_minus[call_back.data])
                current_basket_dict = await self.execute.current_basket(call_back.from_user.id)
                if current_basket_dict is None:
                    await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
                    head_text = 'Ваша корзина пуста 😭😔💔'
                    head_menu_button = {'back': '◀ 👈 Назад'}
                    arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
                    await self.bot.edit_head_caption_by_basket(self.format_text(head_text),
                                                               call_back.message.chat.id,
                                                               arr_messages[0],
                                                               self.build_keyboard(head_menu_button, 1))
                    return number_page
                else:
                    await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
                    pages = {}
                    for page in current_basket_dict.keys():
                        pages[page] = page
                    sum_basket = await self.execute.current_sum_basket(call_back.from_user.id)
                    head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                                f"{self.format_text(self.format_price(float(sum_basket)))}:"
                    head_menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                        'choice_delivery': 'Оформить заказ 📧📦📲'}
                    arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
                    if number_page not in current_basket_dict.keys():
                        new_number = int(number) - 1
                    else:
                        new_number = number
                    number_page_basket = f'{whitespace}Страница №{str(new_number)}'
                    heading = await self.bot.edit_head_caption_by_basket(head_text +
                                                                         self.format_text(number_page_basket),
                                                                         call_back.message.chat.id, arr_messages[0],
                                                                         self.build_keyboard(pages, 3,
                                                                                             head_menu_button))
                    await self.delete_messages(call_back.from_user.id, heading.message_id)
                    arr_answers = []
                    for key, item in current_basket_dict[f'Корзина_Стр.{str(new_number)}'].items():
                        name = await self.execute.current_description(key)
                        text = f"{name[2]}:{whitespace}{self.format_text(str(int(item[0])))} шт. на сумму " \
                               f"{self.format_text(self.format_price(float(item[1])))}"
                        menu_button = {f'{key}basket_minus': '➖', f'{key}basket_plus': '➕', key: 'Подробнее 👀📸'}
                        answer = await self.answer_message_by_basket(heading, text, self.build_keyboard(menu_button, 2))
                        arr_answers.append(str(answer.message_id))
                    await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
                return f'Корзина_Стр.{str(new_number)}'
        except TelegramBadRequest:
            pass
        except IndexError:
            pass

    async def task_basket_plus(self, call_back: CallbackQuery):
        current_page_basket = await self.execute.get_element_history(call_back.from_user.id, -1)
        new_page_basket = await self.plus_amount_basket(call_back, current_page_basket)
        if new_page_basket != current_page_basket:
            await self.execute.delete_element_history(call_back.from_user.id, 1)
            await self.execute.add_element_history(call_back.from_user.id, new_page_basket)
        return True

    async def plus_amount_basket(self, call_back: CallbackQuery, number_page: str):
        try:
            whitespace = '\n'
            number = number_page.split('Корзина_Стр.')[1]
            number_page_basket = f'{whitespace}Страница №{number}'
            current_nomenclature = await self.execute.current_nomenclature_basket(call_back.from_user.id,
                                                                                  self.button_basket_plus[
                                                                                      call_back.data])
            current_amount = current_nomenclature[2]
            current_sum = current_nomenclature[3]
            price = float(current_sum / current_amount)
            availability = await self.execute.current_description(self.button_basket_plus[call_back.data])
            if str(int(current_amount)) == availability[7] or availability[7] == "Нет на складе":
                await self.bot.alert_message(call_back.id, 'Нельзя добавить товара больше, чем есть на остатках!')
            else:
                new_amount = current_amount + 1
                new_sum = new_amount * price
                await self.execute.update_basket_nomenclature(call_back.from_user.id,
                                                              self.button_basket_plus[call_back.data],
                                                              new_amount,
                                                              new_sum)
                name = await self.execute.current_description(self.button_basket_plus[call_back.data])
                text = f"{name[2]}:{whitespace}{self.format_text(str(int(new_amount)))} шт. на сумму " \
                       f"{self.format_text(self.format_price(float(new_sum)))}"
                menu_button = {f'{self.button_basket_plus[call_back.data]}basket_minus': '➖',
                               f'{self.button_basket_plus[call_back.data]}basket_plus': '➕',
                               self.button_basket_plus[call_back.data]: 'Подробнее 👀📸'}
                await self.edit_message_by_basket(call_back.message, text, self.build_keyboard(menu_button, 2))
                current_basket_dict = await self.execute.current_basket(call_back.from_user.id)
                pages = {}
                for page in current_basket_dict.keys():
                    pages[page] = page
                sum_basket = await self.execute.current_sum_basket(call_back.from_user.id)
                head_text = f"Сейчас в Вашу корзину добавлены товары на общую сумму " \
                            f"{self.format_text(self.format_price(float(sum_basket)))}:"
                head_menu_button = {'back': '◀ 👈 Назад', 'clean': 'Очистить корзину 🧹',
                                    'choice_delivery': 'Оформить заказ 📧📦📲'}
                arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
                await self.bot.edit_head_caption_by_basket(head_text + self.format_text(number_page_basket),
                                                           call_back.message.chat.id, arr_messages[0],
                                                           self.build_keyboard(pages, 3, head_menu_button))
            return number_page
        except TelegramBadRequest:
            pass

    async def delete_history_basket(self, id_user: int, delete_item_history: str):
        arr_history = await self.execute.get_arr_history(id_user)
        new_arr_history = []
        for item in arr_history:
            if delete_item_history not in item:
                new_arr_history.append(item)
        await self.execute.update_history(id_user, ' '.join(new_arr_history))

    async def delete_history_delivery(self, id_user: int):
        arr_history = await self.execute.get_arr_history(id_user)
        new_arr_history = arr_history[:-3]
        await self.execute.update_history(id_user, ' '.join(new_arr_history))

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

    async def search(self, text_for_search: list):
        total_search = set()
        i = 1
        for item in text_for_search:
            if i == 1:
                search_variant = await self.execute.search_in_base_article(
                    self.translit_rus(re.sub('\W+', '', item[0]).upper()))
                search_variant_translit_rus = await self.execute.search_in_base_article(
                    self.translit_rus_for_search(re.sub('\W+', '', item[0]).upper()))
                union_variant = search_variant.union(search_variant_translit_rus)
                for variant in item:
                    search_result_by_name = await self.execute.search_in_base_name(variant)
                    search_result_by_name_translit_rus = await self.execute.search_in_base_name(
                        self.translit_rus_for_search(variant))
                    union_search_result_by_name = search_result_by_name.union(search_result_by_name_translit_rus)
                    union_variant.update(union_search_result_by_name)
                total_search = union_variant
                i += 1
            else:
                search_variant = await self.execute.search_in_base_article(
                    self.translit_rus(re.sub('\W+', '', item[0]).upper()))
                search_variant_translit_rus = await self.execute.search_in_base_article(
                    self.translit_rus_for_search(re.sub('\W+', '', item[0]).upper()))
                union_variant = search_variant.union(search_variant_translit_rus)
                for variant in item:
                    search_result_by_name = await self.execute.search_in_base_name(variant)
                    search_result_by_name_translit_rus = await self.execute.search_in_base_name(
                        self.translit_rus_for_search(variant))
                    union_search_result_by_name = search_result_by_name.union(search_result_by_name_translit_rus)
                    union_variant.update(union_search_result_by_name)
                total_search = total_search.intersection(union_variant)
                i += 1
        return self.assembling_search(list(total_search))

    async def task_send_search_result(self, message: Message):
        await self.checking_bot(message)
        result = await self.send_search_result(message)
        return result

    async def send_search_result(self, message: Message):
        if message.content_type == "voice":
            text_for_search = await self.translit_voice(message)
        else:
            text_for_search = message.text
        id_user = message.from_user.id
        change_result = await self.delete_ending(parse(text_for_search))
        result_search = await self.search(change_result)
        current_history = await self.execute.get_element_history(id_user, -1)
        if len(result_search['Поиск_Стр.1']) == 0:
            await self.find_nothing(id_user, message)
            if 'search' in current_history:
                return True
            elif 'Поиск' in current_history:
                await self.execute.delete_element_history(id_user, 1)
                return True
            else:
                await self.execute.add_element_history(id_user,
                                                       f'search___{self.change_record_search(change_result)}')
                return True
        else:
            await self.show_result_search(id_user, message, result_search)
            if 'search' in current_history:
                await self.execute.delete_element_history(id_user, 1)
                await self.execute.add_element_history(id_user,
                                                       f"search___{self.change_record_search(change_result)} "
                                                       f"Поиск_Стр.1")
                return True
            elif 'Поиск' in current_history:
                await self.execute.delete_element_history(id_user, 2)
                await self.execute.add_element_history(id_user,
                                                       f"search___{self.change_record_search(change_result)} "
                                                       f"Поиск_Стр.1")
                return True
            else:
                await self.execute.add_element_history(id_user,
                                                       f"search___{self.change_record_search(change_result)} "
                                                       f"Поиск_Стр.1")
                return True

    async def find_nothing(self, id_user: int, message: Message):
        await self.execute.add_element_message(id_user, message.message_id)
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.bot.push_photo(message.chat.id, self.format_text("Сожалеем, но ничего не найдено."),
                                           self.build_keyboard(menu_button, 1), self.bot.search_logo)
        await self.delete_messages(id_user)
        await self.execute.add_element_message(id_user, answer.message_id)

    async def show_result_search(self, id_user: int, message: Message, result_search: dict):
        await self.execute.add_element_message(id_user, message.message_id)
        number_page = '\n' + 'Страница №1'
        pages = {}
        for page in result_search.keys():
            pages[page] = page
        heading = await self.bot.push_photo(message.chat.id, self.format_text(f"Результаты поиска:{number_page}"),
                                            self.build_keyboard(pages, 3), self.bot.search_logo)
        await self.delete_messages(id_user)
        arr_answers = [str(heading.message_id)]
        for key, value in result_search['Поиск_Стр.1'].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            if value[1]:
                photo = value[1].split()[0]
            else:
                photo = "https://www.rossvik.moscow/images/no_foto.png"
            answer = await self.answer_photo(heading, photo, value[0], self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(id_user, arr_answers)

    async def task_next_page_search(self, call_back: CallbackQuery):
        if await self.next_page_search(call_back):
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def next_page_search(self, call_back: CallbackQuery):
        if self.pages_search[call_back.data] == call_back.message.caption.split('№')[1]:
            return False
        else:
            previous_history = await self.execute.delete_element_history(call_back.from_user.id, 1)
            result_search = await self.search(self.get_text_for_search(previous_history.split('___')[1]))
            pages = {}
            for page in result_search.keys():
                pages[page] = page
            if call_back.message.caption:
                if "Результаты поиска:" in call_back.message.caption:
                    heading = await self.edit_caption_by_basket(call_back.message,
                                                                f"{call_back.message.caption.split('№')[0]}"
                                                                f"№{self.pages_search[call_back.data]}",
                                                                self.build_keyboard(pages, 3))
                    await self.delete_messages(call_back.from_user.id, heading.message_id)
                    arr_answers = []
                else:
                    heading = await self.bot.push_photo(call_back.message.chat.id,
                                                        f"{call_back.message.caption.split('№')[0]}"
                                                        f"№{self.pages_search[call_back.data]}",
                                                        self.build_keyboard(pages, 3), self.bot.search_logo)
                    await self.delete_messages(call_back.from_user.id)
                    arr_answers = [str(heading.message_id)]
            else:
                heading = await self.bot.push_photo(call_back.message.chat.id,
                                                    f"{call_back.message.caption.split('№')[0]}"
                                                    f"№{self.pages_search[call_back.data]}",
                                                    self.build_keyboard(pages, 3), self.bot.search_logo)
                await self.delete_messages(call_back.from_user.id)
                arr_answers = [str(heading.message_id)]
            for key, value in result_search[call_back.data].items():
                menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
                if value[1]:
                    photo = value[1].split()[0]
                else:
                    photo = "https://www.rossvik.moscow/images/no_foto.png"
                answer = await self.answer_photo(heading, photo, value[0], self.build_keyboard(menu_button, 2))
                arr_answers.append(str(answer.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
            return True

    async def return_page_search(self, call_back: CallbackQuery, result_search: dict, current_page: str):
        number_page = '\n' + 'Страница №' + self.pages_search[current_page]
        pages = {}
        for page in result_search.keys():
            pages[page] = page
        if call_back.message.caption:
            if "Результаты поиска:" in call_back.message.caption:
                heading = await self.edit_caption_by_basket(call_back.message,
                                                            self.format_text(f"Результаты поиска:{number_page}"),
                                                            self.build_keyboard(pages, 3))
                await self.delete_messages(call_back.from_user.id, heading.message_id)
                arr_answers = []
            else:
                heading = await self.bot.push_photo(call_back.message.chat.id,
                                                    self.format_text(f"Результаты поиска:{number_page}"),
                                                    self.build_keyboard(pages, 3), self.bot.search_logo)
                await self.delete_messages(call_back.from_user.id)
                arr_answers = [str(heading.message_id)]
        else:
            heading = await self.bot.push_photo(call_back.message.chat.id,
                                                self.format_text(f"Результаты поиска:{number_page}"),
                                                self.build_keyboard(pages, 3), self.bot.search_logo)
            await self.delete_messages(call_back.from_user.id)
            arr_answers = [str(heading.message_id)]
        for key, value in result_search[current_page].items():
            menu_button = {'back': '◀ 👈 Назад', key: 'Подробнее 👀📸', f'{key}add': 'Добавить ✅🗑️'}
            if value[1]:
                photo = value[1].split()[0]
            else:
                photo = "https://www.rossvik.moscow/images/no_foto.png"
            answer = await self.answer_photo(heading, photo, value[0], self.build_keyboard(menu_button, 2))
            arr_answers.append(str(answer.message_id))
        await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)

    async def translit_voice(self, message: Message):
        try:
            result = ""
            voice_path = await self.bot.save_voice(message)
            key_id = os.environ["KeyId"]
            key_secret = os.environ["KeySecret"]
            headers = {"keyId": key_id, "keySecret": key_secret}
            create_url = "https://api.speechflow.io/asr/file/v1/create?lang=ru"
            query_url = "https://api.speechflow.io/asr/file/v1/query?taskId="
            files = {"file": open(voice_path, "rb")}
            response = requests.post(create_url, headers=headers, files=files)
            if response.status_code == 200:
                create_result = response.json()
                query_url += create_result["taskId"] + "&resultType=4"
                while True:
                    response = requests.get(query_url, headers=headers)
                    if response.status_code == 200:
                        query_result = response.json()
                        if query_result["code"] == 11000:
                            if query_result["result"]:
                                result = query_result["result"].replace("\n\n", " ")
                            break
                        elif query_result["code"] == 11001:
                            continue
                        else:
                            break
                    else:
                        break
            return result
        except ConnectionError:
            result = ""
            return result

    @staticmethod
    async def delete_ending(text_for_search: str):
        arr_text = text_for_search.split()
        text_dict = {}
        new_text_list = []
        i = 0
        for item in arr_text:
            string_delete_end = snowball.stem(item)
            new_item = re.sub('\W+', '', string_delete_end)
            if new_item != '':
                text_dict[new_item] = new_item
                text_dict[new_item.lower()] = new_item.lower()
                text_dict[new_item.title()] = new_item.title()
                new_text_list.append([])
                for value in text_dict.values():
                    new_text_list[i].append(value)
                text_dict = {}
                i += 1
        return new_text_list

    @staticmethod
    def assembling_search(arr: list):
        assembling_dict_search = {}
        dict_m = {}
        i = 1
        y = 1
        for item_nomenclature in sorted(arr, key=itemgetter(2), reverse=False):
            if i < 7:
                dict_m[item_nomenclature[0]] = [item_nomenclature[1], item_nomenclature[3]]
                i += 1

            else:
                assembling_dict_search['Поиск_Стр.' + str(y)] = dict_m
                i = 1
                dict_m = {}
                y += 1
                dict_m[item_nomenclature[0]] = [item_nomenclature[1], item_nomenclature[3]]
                i += 1
        assembling_dict_search['Поиск_Стр.' + str(y)] = dict_m
        return assembling_dict_search

    @staticmethod
    def change_record_search(arr_text_search: list):
        arr_value = []
        for item in arr_text_search:
            string_value = '///'.join(item)
            arr_value.append(string_value)
        result_string = '/////'.join(arr_value)
        return result_string

    @staticmethod
    def get_text_for_search(text: str):
        arr_result = []
        list_search = text.split('/////')
        for value in list_search:
            arr_result.append(value.split('///'))
        return arr_result

    async def task_choice_delivery_user(self, call_back: CallbackQuery):
        await self.delete_messages(call_back.from_user.id, call_back.message.message_id)
        await self.choice_delivery_user(call_back)
        await self.execute.add_element_history(call_back.from_user.id, 'choice_delivery')
        return True

    async def choice_delivery_user(self, call_back: CallbackQuery):
        head_menu_button = {'pickup': 'Самовывоз 🖐🏻', 'delivery': 'Доставка 📦', 'back': '◀ 👈 Назад'}
        head_text = f"Выберете вариант получения товара:"
        if call_back.message.caption:
            answer = await self.answer_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
            await self.execute.delete_new_order(call_back.from_user.id)

    async def task_pickup_or_delivery(self, call_back: CallbackQuery):
        if call_back.data == 'pickup':
            await self.pickup(call_back)
        elif call_back.data == 'delivery':
            await self.delivery(call_back)
        await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def pickup(self, call_back: CallbackQuery):
        await self.execute.delete_new_order(call_back.from_user.id)
        head_menu_button = {'record_answer_shop': 'Москва, Хачатуряна, 8 корпус 3 (Магазин)',
                            'record_answer_storage': 'Мытищи, 1-ая Новая, 57 (Склад)',
                            'back': '◀ 👈 Назад'}
        head_text = f"Выберете откуда будете забирать товар:"
        if call_back.message.caption:
            answer = await self.answer_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        await self.execute.record_new_order(call_back.from_user.id, 'Самовывоз 🖐🏻')

    async def delivery(self, call_back: CallbackQuery):
        await self.execute.delete_new_order(call_back.from_user.id)
        head_menu_button = {'record_answer_moscow': 'В пределах МКАД',
                            'record_answer_pek': 'ТК ПЭК',
                            'record_answer_dl': 'ТК Деловые Линии',
                            'record_answer_mt': 'ТК Мейджик Транс',
                            'record_answer_cdek': 'ТК СДЭК',
                            'back': '◀ 👈 Назад'}
        head_text = f"Выберете какой транспортной компанией доставить товар, " \
                    f"либо можем доставить товар своими силами в пределах МКАД:"
        if call_back.message.caption:
            answer = await self.answer_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.edit_message(call_back.message, head_text, self.build_keyboard(head_menu_button, 1))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        await self.execute.record_new_order(call_back.from_user.id, 'Доставка 📦')

    async def task_record_answer_pickup(self, call_back: CallbackQuery):
        await self.record_answer_pickup(call_back)
        await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def record_answer_pickup(self, call_back: CallbackQuery, kind_pickup: str = None):
        whitespace = '\n'
        if kind_pickup is None:
            kind_pickup = call_back.data
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        if info_order[9] == '':
            amount_content = 0
        else:
            amount_content = len(info_order[9].split('///'))
        arr_messages = info_order[8].split('///')
        string_messages = '\n'.join(arr_messages)
        head_menu_button = {'back': '◀ 👈 Назад', 'new_attachments': f'Вложения 🗃️ ({str(amount_content)})',
                            'post': 'Отправить заказ 📫'}
        button_fill_details = {'fill_details': 'Заполнить реквизиты 📝'}
        if info_order[10] == '':
            message_text = 'Заполните реквизиты для отправки заказа!'
            head_text = f"{self.format_text(message_text)}{whitespace}" \
                        f"Способ доставки: {self.format_text(info_order[6])}{whitespace}" \
                        f"TK или пункт самовывоза: {self.format_text(self.kind_pickup[kind_pickup])}{whitespace}" \
                        f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                        f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                        f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                        f"Телефон: {self.format_text(info_order[13])}{whitespace}" \
                        f"Комментарий: {self.format_text(string_messages)}"
        else:
            head_text = f"Способ доставки: {self.format_text(info_order[6])}{whitespace}" \
                        f"TK или пункт самовывоза: {self.format_text(self.kind_pickup[kind_pickup])}{whitespace}" \
                        f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                        f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                        f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                        f"Телефон: {self.format_text(info_order[13])}{whitespace}" \
                        f"Комментарий: {self.format_text(string_messages)}"
        if call_back.message.caption:
            answer = await self.answer_message_by_basket(call_back.message, head_text,
                                                         self.build_keyboard(head_menu_button, 2,
                                                                             button_fill_details))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.edit_message_by_basket(call_back.message, head_text,
                                                       self.build_keyboard(head_menu_button, 2,
                                                                           button_fill_details))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        arr_contact = await self.execute.get_contact_user(call_back.from_user.id, self.kind_pickup[kind_pickup])
        if len(arr_contact) != 0:
            arr_answers = []
            for contact in arr_contact:
                if contact[4] == '':
                    amount_content = 0
                else:
                    amount_content = len(contact[4].split('///'))
                arr_messages = contact[3].split('///')
                string_messages = '\n'.join(arr_messages)
                menu_contact = {f'choice_contact{contact[0]}': 'Выбрать эти реквизиты ✅',
                                f'delete_record{contact[0]}': 'Удалить запись 🗑️',
                                f'nested{contact[0]}': f'Вложения 🗃️ ({str(amount_content)})',
                                'back': '◀ 👈 Назад'}
                text_contact = f"Способ доставки: {self.format_text(contact[1])}{whitespace}" \
                               f"TK или пункт самовывоза: {self.format_text(contact[2])}" \
                               f"{whitespace}" \
                               f"ИНН: {self.format_text(contact[5])}{whitespace}" \
                               f"ФИО или наименование компании: {self.format_text(contact[6])}" \
                               f"{whitespace}" \
                               f"E-mail: {self.format_text(contact[7])}{whitespace}" \
                               f"Телефон: {self.format_text(contact[8])}{whitespace}" \
                               f"Комментарий: {self.format_text(string_messages)}"
                answer_contact = await self.answer_message_by_basket(answer, text_contact,
                                                                     self.build_keyboard(menu_contact, 1))
                arr_answers.append(str(answer_contact.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
        await self.execute.record_order_kind_transport_company(call_back.from_user.id,
                                                               self.kind_pickup[kind_pickup])

    async def task_record_answer_delivery(self, call_back: CallbackQuery):
        await self.record_answer_delivery(call_back)
        await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def record_answer_delivery(self, call_back: CallbackQuery, kind_delivery: str = None):
        whitespace = '\n'
        if kind_delivery is None:
            kind_delivery = call_back.data
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        if info_order[9] == '':
            amount_content = 0
        else:
            amount_content = len(info_order[9].split('///'))
        arr_messages = info_order[8].split('///')
        string_messages = '\n'.join(arr_messages)
        head_menu_button = {'back': '◀ 👈 Назад', 'new_attachments': f'Вложения 🗃️ ({str(amount_content)})',
                            'post': 'Отправить заказ 📫'}
        button_fill_details = {'fill_details': 'Заполнить реквизиты 📝'}
        if info_order[10] == '':
            message_text = 'Заполните реквизиты для отправки заказа!'
            head_text = f"{self.format_text(message_text)}{whitespace}" \
                        f"Способ доставки: {self.format_text(info_order[6])}{whitespace}" \
                        f"TK или пункт самовывоза: {self.format_text(self.kind_delivery[kind_delivery])}{whitespace}" \
                        f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                        f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                        f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                        f"Телефон: {self.format_text(info_order[13])}{whitespace}" \
                        f"Комментарий: {self.format_text(string_messages)}"
        else:
            head_text = f"Способ доставки: {self.format_text(info_order[6])}{whitespace}" \
                        f"TK или пункт самовывоза: {self.format_text(self.kind_delivery[kind_delivery])}{whitespace}" \
                        f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                        f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                        f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                        f"Телефон: {self.format_text(info_order[13])}{whitespace}" \
                        f"Комментарий: {self.format_text(string_messages)}"
        if call_back.message.caption:
            answer = await self.answer_message_by_basket(call_back.message, head_text,
                                                         self.build_keyboard(head_menu_button, 2,
                                                                             button_fill_details))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.edit_message_by_basket(call_back.message, head_text,
                                                       self.build_keyboard(head_menu_button, 2,
                                                                           button_fill_details))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        arr_contact = await self.execute.get_contact_user(call_back.from_user.id, self.kind_delivery[kind_delivery])
        if len(arr_contact) != 0:
            arr_answers = []
            for contact in arr_contact:
                if contact[4] == '':
                    amount_content = 0
                else:
                    amount_content = len(contact[4].split('///'))
                arr_messages = contact[3].split('///')
                string_messages = '\n'.join(arr_messages)
                menu_contact = {f'choice_contact{contact[0]}': 'Выбрать эти реквизиты ✅',
                                f'delete_record{contact[0]}': 'Удалить запись 🗑️',
                                f'nested{contact[0]}': f'Вложения 🗃️ ({str(amount_content)})',
                                'back': '◀ 👈 Назад'}
                text_contact = f"Способ доставки: {self.format_text(contact[1])}{whitespace}" \
                               f"TK или пункт самовывоза: {self.format_text(contact[2])}" \
                               f"{whitespace}" \
                               f"ИНН: {self.format_text(contact[5])}{whitespace}" \
                               f"ФИО или наименование компании: {self.format_text(contact[6])}" \
                               f"{whitespace}" \
                               f"E-mail: {self.format_text(contact[7])}{whitespace}" \
                               f"Телефон: {self.format_text(contact[8])}{whitespace}" \
                               f"Комментарий: {self.format_text(string_messages)}"
                answer_contact = await self.answer_message_by_basket(answer, text_contact,
                                                                     self.build_keyboard(menu_contact, 1))
                arr_answers.append(str(answer_contact.message_id))
            await self.execute.add_arr_messages(call_back.from_user.id, arr_answers)
        await self.execute.record_order_kind_transport_company(call_back.from_user.id,
                                                               self.kind_delivery[kind_delivery])

    async def task_content_type_text(self, message: Message):
        await self.record_message_comment_user(message)
        await self.change_head_message_by_media(message.from_user.id)
        arr_message = await self.get_answer(message)
        await self.bot.delete_messages_chat(message.chat.id, arr_message[1:])
        return True

    async def record_message_comment_user(self, message: Message):
        order_info = await self.execute.get_info_order(message.from_user.id)
        await self.change_comment(message.from_user.id, message.text, order_info[8])

    async def get_document(self, message: Message):
        document_info = await self.bot.save_document(message)
        arr_message = await self.get_answer(message)
        await self.bot.delete_messages_chat(message.chat.id, arr_message[1:])
        return document_info

    async def get_audio(self, message: Message):
        audio_info = await self.bot.save_audio(message)
        arr_message = await self.get_answer(message)
        await self.bot.delete_messages_chat(message.chat.id, arr_message[1:])
        return audio_info

    async def get_voice(self, message: Message):
        voice_info = await self.bot.save_voice(message)
        arr_message = await self.get_answer(message)
        await self.bot.delete_messages_chat(message.chat.id, arr_message[1:])
        return voice_info

    async def get_photo(self, message: Message):
        photo_info = await self.bot.save_photo(message)
        arr_message = await self.get_answer(message)
        await self.bot.delete_messages_chat(message.chat.id, arr_message[1:])
        return photo_info

    async def get_video(self, message: Message):
        video_info = await self.bot.save_photo(message)
        arr_message = await self.get_answer(message)
        await self.bot.delete_messages_chat(message.chat.id, arr_message[1:])
        return video_info

    async def record_comment_and_content(self, info_media: tuple, info_order: list):
        comment = await self.add_element(info_media[1], info_order[0])
        content = await self.add_element(info_media[0], info_order[1])
        return comment, content

    async def get_answer(self, message: Message):
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        arr_messages.append(str(message.message_id))
        return arr_messages

    async def add_element(self, new_element: str, current_element: str):
        if new_element is None:
            total_element = current_element
        else:
            if current_element == '':
                total_element = new_element
            else:
                arr_text_from_user = self.get_arr_message_user(current_element)
                new_arr_message_from_user = self.add_message_user(arr_text_from_user, new_element)
                new_string_comment = self.get_arr_messages_user_for_record(new_arr_message_from_user)
                total_element = new_string_comment
        return total_element

    async def change_comment(self, user_id: int, new_comment: str, current_comment: str):
        if current_comment == '':
            await self.execute.record_order_comment(user_id, new_comment)
        else:
            arr_text_from_user = self.get_arr_message_user(current_comment)
            new_arr_message_from_user = self.add_message_user(arr_text_from_user, new_comment)
            new_string_comment = self.get_arr_messages_user_for_record(new_arr_message_from_user)
            await self.execute.record_order_comment(user_id, new_string_comment)

    async def change_head_message_by_media(self, user_id: int):
        try:
            whitespace = '\n'
            arr_messages = await self.execute.get_arr_messages(user_id)
            head_message = arr_messages[0]
            info_order = await self.execute.get_info_order(user_id)
            if info_order[9] == '':
                amount_content = 0
            else:
                amount_content = len(info_order[9].split('///'))
            arr_messages = info_order[8].split('///')
            string_messages = '\n'.join(arr_messages)
            head_menu_button = {'back': '◀ 👈 Назад', 'new_attachments': f'Вложения 🗃️ ({str(amount_content)})',
                                'post': 'Отправить заказ 📫'}
            button_fill_details = {'fill_details': 'Заполнить реквизиты 📝'}
            change_text_head = f"Способ доставки: {self.format_text(info_order[6])}{whitespace}" \
                               f"TK или пункт самовывоза: {self.format_text(info_order[7])}{whitespace}" \
                               f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                               f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                               f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                               f"Телефон: {self.format_text(info_order[13])}{whitespace}" \
                               f"Комментарий: {self.format_text(string_messages)}"
            await self.bot.edit_head_message_by_basket(change_text_head, user_id, head_message,
                                                       self.build_keyboard(head_menu_button, 2, button_fill_details))
        except TelegramBadRequest:
            arr_messages = await self.execute.get_arr_messages(user_id)
            head_message = arr_messages[0]
            info_order = await self.execute.get_info_order(user_id)
            if info_order[9] == '':
                amount_content = 0
            else:
                amount_content = len(info_order[9].split('///'))
            head_menu_button = {'back': '◀ 👈 Назад', 'new_attachments': f'Вложения 🗃️ ({str(amount_content)})',
                                'post': 'Отправить заказ 📫'}
            button_fill_details = {'fill_details': 'Заполнить реквизиты 📝'}
            await self.bot.edit_head_keyboard(user_id, head_message, self.build_keyboard(head_menu_button, 2,
                                                                                         button_fill_details))

    async def task_show_new_attachments(self, call_back: CallbackQuery):
        check = await self.show_new_attachments(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def show_new_attachments(self, call_back: CallbackQuery):
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        if info_order[9] == '':
            return False
        else:
            arr_attachments = info_order[9].split('///')
            i = 0
            arr = []
            arr_message = []
            for media in arr_attachments:
                if i == 10:
                    arr_media_message = await self.send_media(call_back.message, arr)
                    for item in arr_media_message:
                        arr_message.append(str(item.message_id))
                    i = 0
                    arr = [media]
                    i += 1
                else:
                    arr.append(media)
                    i += 1
            arr_media_message = await self.send_media(call_back.message, arr)
            for item in arr_media_message:
                arr_message.append(str(item.message_id))
            menu_button = {'back': '◀ 👈 Назад'}
            text = 'Вложенные файлы.\n' \
                   'Нажмите на кнопку ниже, чтобы вернуться к отправке заказа!'
            answer_return = await self.answer_message(call_back.message, self.format_text(text),
                                                      self.build_keyboard(menu_button, 1))
            arr_message.append(str(answer_return.message_id))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_arr_messages(call_back.from_user.id, arr_message)
            return True

    async def task_show_nested(self, call_back: CallbackQuery):
        check = await self.show_nested(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def show_nested(self, call_back: CallbackQuery, current: str = None):
        if current:
            number_order = current.split('nested')[1]
        else:
            number_order = call_back.data.split('nested')[1]
        content = await self.execute.get_content_order_user(number_order)
        if content[0] == '':
            check_amount = False
        else:
            arr_attachments = content[0].split('///')
            i = 0
            arr = []
            arr_message = []
            for media in arr_attachments:
                if i == 10:
                    arr_media_message = await self.send_media(call_back.message, arr)
                    for item in arr_media_message:
                        arr_message.append(str(item.message_id))
                    i = 0
                    arr = [media]
                    i += 1
                else:
                    arr.append(media)
                    i += 1
            arr_media_message = await self.send_media(call_back.message, arr)
            for item in arr_media_message:
                arr_message.append(str(item.message_id))
            menu_button = {'back': '◀ 👈 Назад'}
            text = 'Вложенные файлы.\n' \
                   'Нажмите на кнопку ниже, чтобы вернуться к отправке заказа!'
            answer_return = await self.answer_message(call_back.message, self.format_text(text),
                                                      self.build_keyboard(menu_button, 1))
            arr_message.append(str(answer_return.message_id))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_arr_messages(call_back.from_user.id, arr_message)
            check_amount = True
        return check_amount

    async def task_choice_comment_user(self, call_back: CallbackQuery):
        check = await self.choice_comment_user(call_back)
        return check

    async def choice_comment_user(self, call_back: CallbackQuery):
        arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
        head_message = arr_messages[0]
        number_order = call_back.data.split('choice_contact')[1]
        info_choice_order = await self.execute.get_info_order_by_number(call_back.from_user.id, number_order)
        info_current_order = await self.execute.get_comment_content_order_user(call_back.from_user.id)
        info_for_record = await self.record_comment_and_content(info_choice_order, info_current_order)
        if info_for_record[1] == '':
            amount_content = '0'
        else:
            amount_content = len(info_for_record[1].split('///'))
        if info_for_record[0] == '':
            text_head = f"{self.format_text('Нет сообщений для отправки вместе с заказом')}"
        else:
            arr_messages = info_for_record[0].split('///')
            string_messages = '\n'.join(arr_messages)
            text_head = f"Сообщение для отправки вместе с заказом:\n{self.format_text(string_messages)}"
        head_menu_button = {'back': '◀ 👈 Назад', 'new_attachments': f'Вложения 🗃️ ({str(amount_content)})',
                            'post': 'Отправить заказ 📫'}
        button_fill_details = {'fill_details': 'Заполнить реквизиты 📝'}
        await self.bot.edit_head_message_by_basket(text_head, call_back.message.chat.id, int(head_message),
                                                   self.build_keyboard(head_menu_button, 2, button_fill_details))
        await self.execute.record_order_comment_and_content(call_back.from_user.id, info_for_record[0],
                                                            info_for_record[1])
        await self.delete_messages(call_back.from_user.id, head_message)
        return True

    async def delete_record_user(self, call_back: CallbackQuery):
        await self.delete_messages(call_back.from_user.id, call_back.message.message_id, True)
        return True

    async def task_fill_details(self, call_back: CallbackQuery):
        check = await self.fill_details(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def fill_details(self, call_back: CallbackQuery):
        menu_button = {'private_person': 'Частное лицо 👱 👩',
                       'individual_entrepreneur': f'ИП, ООО, ОАО, ЗАО 👨‍💼 👩‍💼 🏭'}
        back_button = {'back': '◀ 👈 Назад'}
        text = 'Выберите организационно-правовую форму:'
        if call_back.message.caption:
            answer = await self.answer_message(call_back.message, text, self.build_keyboard(menu_button, 1,
                                                                                            back_button))
            await self.delete_messages(call_back.from_user.id)
            await self.execute.add_element_message(call_back.from_user.id, answer.message_id)
        else:
            answer = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 1, back_button))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
        await self.execute.record_order_inn_company(call_back.from_user.id, '')
        return True

    async def task_private_person(self, call_back: CallbackQuery):
        check = await self.private_person(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def private_person(self, call_back: CallbackQuery):
        whitespace = '\n'
        await self.execute.record_order_name_company(call_back.from_user.id, '')
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        back_button = {'forward_email': 'Заполнить E-mail @ 📬', 'back': '◀ 👈 Назад'}
        text = 'Отправьте сообщение с ФИО физического лица, который будет указан как покупатель (получатель).'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text('Частное лицо')}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        answer = await self.edit_message_by_basket(call_back.message, change_text_head,
                                                   self.build_keyboard(back_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)
        await self.execute.record_order_inn_company(call_back.from_user.id, 'Частное лицо')
        return True

    async def task_record_name(self, message: Message):
        check = await self.record_name(message)
        return check

    async def record_name(self, message: Message):
        whitespace = '\n'
        info_order = await self.execute.get_info_order(message.from_user.id)
        back_button = {'forward_email': 'Заполнить E-mail @ 📬', 'back': '◀ 👈 Назад'}
        name_company = await self.check_text(message.text)
        text = 'Отправьте сообщение с ФИО физического лица, который будет указан как покупатель (получатель).'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(name_company)}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        head_message = arr_messages[0]
        try:
            await self.bot.edit_head_message_by_basket(change_text_head, message.from_user.id, head_message,
                                                       self.build_keyboard(back_button, 1))
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_name_company(message.from_user.id, name_company)
            return True
        except TelegramBadRequest:
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_name_company(message.from_user.id, name_company)
            return True

    async def task_individual_entrepreneur(self, call_back: CallbackQuery):
        check = await self.individual_entrepreneur(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def individual_entrepreneur(self, call_back: CallbackQuery):
        whitespace = '\n'
        await self.execute.record_order_inn_company(call_back.from_user.id, '')
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        back_button = {'forward_name_company': 'Заполнить наименование компании ✍', 'back': '◀ 👈 Назад'}
        text = 'Отправьте сообщение с номером ИНН.'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        answer = await self.edit_message_by_basket(call_back.message, change_text_head,
                                                   self.build_keyboard(back_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)
        return True

    async def task_record_inn(self, message: Message):
        check = await self.record_inn(message)
        return check

    async def record_inn(self, message: Message):
        whitespace = '\n'
        info_order = await self.execute.get_info_order(message.from_user.id)
        back_button = {'forward_name_company': 'Заполнить наименование компании ✍', 'back': '◀ 👈 Назад'}
        inn_company = await self.check_inn(message.text)
        text = 'Отправьте сообщение с номером ИНН.'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(inn_company)}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        head_message = arr_messages[0]
        try:
            await self.bot.edit_head_message_by_basket(change_text_head, message.from_user.id, head_message,
                                                       self.build_keyboard(back_button, 1))
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_inn_company(message.from_user.id, inn_company)
            return True
        except TelegramBadRequest:
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_inn_company(message.from_user.id, inn_company)
            return True

    async def task_forward_name_company(self, call_back: CallbackQuery):
        check = await self.forward_name_company(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def forward_name_company(self, call_back: CallbackQuery):
        whitespace = '\n'
        await self.execute.record_order_name_company(call_back.from_user.id, '')
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        if is_valid(info_order[10]):
            back_button = {'forward_email': 'Заполнить E-mail @ 📬', 'back': '◀ 👈 Назад'}
            text = 'Отправьте сообщение с наименованием компании, которое будет указано как покупатель (получатель).'
            change_text_head = f"{self.format_text(text)}{whitespace}" \
                               f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                               f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                               f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                               f"Телефон: {self.format_text(info_order[13])}"
            answer = await self.edit_message_by_basket(call_back.message, change_text_head,
                                                       self.build_keyboard(back_button, 1))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
            return True
        else:
            await self.bot.alert_message(call_back.id, 'Недопустимый номер ИНН')
            return False

    async def task_record_name_company(self, message: Message):
        check = await self.record_name_company(message)
        return check

    async def record_name_company(self, message: Message):
        whitespace = '\n'
        info_order = await self.execute.get_info_order(message.from_user.id)
        back_button = {'forward_email': 'Заполнить E-mail @ 📬', 'back': '◀ 👈 Назад'}
        name_company = await self.check_text(message.text)
        text = 'Отправьте сообщение с наименованием компании, которое будет указано как покупатель (получатель).'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(name_company)}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        head_message = arr_messages[0]
        try:
            await self.bot.edit_head_message_by_basket(change_text_head, message.from_user.id, head_message,
                                                       self.build_keyboard(back_button, 1))
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_name_company(message.from_user.id, name_company)
            return True
        except TelegramBadRequest:
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_name_company(message.from_user.id, name_company)
            return True

    async def task_forward_email(self, call_back: CallbackQuery):
        check = await self.forward_email(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def forward_email(self, call_back: CallbackQuery):
        whitespace = '\n'
        await self.execute.record_order_email_company(call_back.from_user.id, '')
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        back_button = {'forward_telephone': 'Заполнить телефон 📞 📲', 'back': '◀ 👈 Назад'}
        text = 'Отправьте сообщение с E-mail, он нужен нам, чтобы мы могли связаться с Вами в случае необходимости.'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        answer = await self.edit_message_by_basket(call_back.message, change_text_head,
                                                   self.build_keyboard(back_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)
        return True

    async def task_record_email(self, message: Message):
        check = await self.record_email(message)
        return check

    async def record_email(self, message: Message):
        whitespace = '\n'
        info_order = await self.execute.get_info_order(message.from_user.id)
        back_button = {'forward_telephone': 'Заполнить телефон 📞 📲', 'back': '◀ 👈 Назад'}
        email_company = await self.check_email(message.text)
        text = 'Отправьте сообщение с E-mail, он нужен нам, чтобы мы могли связаться с Вами в случае необходимости.'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                           f"E-mail: {self.format_text(email_company)}{whitespace}" \
                           f"Телефон: {self.format_text(info_order[13])}"
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        head_message = arr_messages[0]
        try:
            await self.bot.edit_head_message_by_basket(change_text_head, message.from_user.id, head_message,
                                                       self.build_keyboard(back_button, 1))
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_email_company(message.from_user.id, email_company)
            return True
        except TelegramBadRequest:
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_email_company(message.from_user.id, email_company)
            return True

    async def task_forward_telephone(self, call_back: CallbackQuery):
        check = await self.forward_telephone(call_back)
        if check:
            await self.execute.add_element_history(call_back.from_user.id, call_back.data)
        return True

    async def forward_telephone(self, call_back: CallbackQuery):
        whitespace = '\n'
        await self.execute.record_order_telephone_company(call_back.from_user.id, '')
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        if validate_email(info_order[12], verify=True):
            back_button = {'forward_done': 'Готово ✔️', 'back': '◀ 👈 Назад'}
            text = 'Отправьте сообщение с номером телефона, на который мы можем написать Вам, если это потребуется.'
            change_text_head = f"{self.format_text(text)}{whitespace}" \
                               f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                               f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                               f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                               f"Телефон: {self.format_text(info_order[13])}"
            answer = await self.edit_message_by_basket(call_back.message, change_text_head,
                                                       self.build_keyboard(back_button, 1))
            await self.delete_messages(call_back.from_user.id, answer.message_id)
            return True
        else:
            await self.bot.alert_message(call_back.id, 'Недопустимый адрес электронной почты!')
            return False

    async def task_record_telephone(self, message: Message):
        check = await self.record_telephone(message)
        return check

    async def record_telephone(self, message: Message):
        whitespace = '\n'
        info_order = await self.execute.get_info_order(message.from_user.id)
        back_button = {'forward_done': 'Готово ✔️', 'back': '◀ 👈 Назад'}
        telephone_company = await self.check_telephone(message.text)
        text = 'Отправьте сообщение с номером телефона, на который мы можем написать Вам, если это потребуется.'
        change_text_head = f"{self.format_text(text)}{whitespace}" \
                           f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                           f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                           f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                           f"Телефон: {self.format_text(telephone_company)}"
        arr_messages = await self.execute.get_arr_messages(message.from_user.id)
        head_message = arr_messages[0]
        try:
            await self.bot.edit_head_message_by_basket(change_text_head, message.from_user.id, head_message,
                                                       self.build_keyboard(back_button, 1))
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_telephone_company(message.from_user.id, telephone_company)
            return True
        except TelegramBadRequest:
            await self.bot.delete_messages_chat(message.chat.id, [message.message_id])
            await self.execute.record_order_telephone_company(message.from_user.id, telephone_company)
            return True

    async def task_forward_done(self, call_back: CallbackQuery):
        check = await self.forward_done(call_back)
        if check:
            await self.execute.delete_element_history_before_value(call_back.from_user.id, 'fill_details')
        return True

    async def forward_done(self, call_back: CallbackQuery):
        whitespace = '\n'
        info_order = await self.execute.get_info_order(call_back.from_user.id)
        if self.validate_phone_number(info_order[13]):
            arr_messages = await self.execute.get_arr_messages(call_back.from_user.id)
            head_message = arr_messages[0]
            if info_order[9] == '':
                amount_content = 0
            else:
                amount_content = len(info_order[9].split('///'))
            arr_messages = info_order[8].split('///')
            string_messages = '\n'.join(arr_messages)
            head_menu_button = {'back': '◀ 👈 Назад', 'new_attachments': f'Вложения 🗃️ ({str(amount_content)})',
                                'post': 'Отправить заказ 📫'}
            button_fill_details = {'fill_details': 'Заполнить реквизиты 📝'}
            change_text_head = f"Способ доставки: {self.format_text(info_order[6])}{whitespace}" \
                               f"TK или пункт самовывоза: {self.format_text(info_order[7])}{whitespace}" \
                               f"ИНН: {self.format_text(info_order[10])}{whitespace}" \
                               f"ФИО или наименование компании: {self.format_text(info_order[11])}{whitespace}" \
                               f"E-mail: {self.format_text(info_order[12])}{whitespace}" \
                               f"Телефон: {self.format_text(info_order[13])}{whitespace}" \
                               f"Комментарий: {self.format_text(string_messages)}"
            await self.bot.edit_head_message_by_basket(change_text_head, call_back.from_user.id, head_message,
                                                       self.build_keyboard(head_menu_button, 2, button_fill_details))
            return True
        else:
            await self.bot.alert_message(call_back.id, 'Несуществующий номер телефона!')
            return False

    @staticmethod
    async def check_inn(string_text: str):
        inn = re.sub("[^0-9]", "", string_text)
        return inn

    @staticmethod
    async def check_text(string_text: str):
        arr_text = string_text.split(' ')
        new_arr_text = []
        for item in arr_text:
            new_item = re.sub('\W+', '', item)
            if new_item != '':
                new_arr_text.append(new_item)
        new_string = ' '.join(new_arr_text)
        return new_string

    @staticmethod
    async def check_email(string_text: str):
        arr_text = string_text.split(' ')
        new_arr_text = []
        for item in arr_text:
            new_item = re.sub("[^A-Za-z@.]", "", item)
            if new_item != '':
                new_arr_text.append(new_item)
        new_string = ' '.join(new_arr_text)
        return new_string

    @staticmethod
    async def check_telephone(string_text: str):
        telephone = re.sub("[^0-9+]", "", string_text)
        if telephone[0] != '+' and len(telephone) == 10:
            telephone = '+7' + telephone
        elif len(telephone) == 11:
            telephone = '+7' + telephone[1:]
        return telephone

    @staticmethod
    def validate_phone_number(potential_number: str) -> bool:
        try:
            phone_number_obj = phonenumbers.parse(potential_number)
        except phonenumbers.phonenumberutil.NumberParseException:
            return False
        if not phonenumbers.is_valid_number(phone_number_obj):
            return False
        return True

    async def task_post_admin(self, call_back: CallbackQuery):
        await self.post_admin(call_back)
        await self.delete_history_delivery(call_back.from_user.id)
        return True

    async def post_admin(self, call_back: CallbackQuery):
        info_order = await self.record_data_order_by_xlsx(call_back)
        list_user_admin = await self.execute.get_user_admin
        menu_button = {'attachments': 'Показать вложения', 'take_order': '💬 Взять заказ в обработку'}
        info_delivery_address_from_user = await self.execute.get_delivery_address(call_back.from_user.id)
        if info_delivery_address_from_user[2] == '':
            comment = 'Частное лицо'
        else:
            comment = '\n'.join(info_delivery_address_from_user[2].split('///'))
        list_messages_admins = []
        for user in list_user_admin:
            answer = await self.bot.send_message_order(int(user[0]),
                                                       f'{call_back.from_user.id} '
                                                       f'{call_back.from_user.first_name} '
                                                       f'{call_back.from_user.last_name} '
                                                       f'{call_back.from_user.username} ',
                                                       info_order[1],
                                                       f"\n{info_delivery_address_from_user[0]}\n"
                                                       f"{info_delivery_address_from_user[1]}\n"
                                                       f"{comment}",
                                                       info_order[0],
                                                       self.build_keyboard(menu_button, 1))
            list_messages_admins.append(str(answer.message_id))
        await self.execute.record_order_answer_admin(call_back.from_user.id,
                                                     info_order[0],
                                                     ' '.join(list_messages_admins))
        await self.execute.clean_basket(call_back.from_user.id)
        text = 'Мы получили заказ, в ближайшее время пришлем Вам счет для оплаты или свяжемся с Вами, ' \
               'если у нас появятся вопросы 😎👌🔥'
        menu_button = {'back': '◀ 👈 Назад'}
        answer = await self.edit_message(call_back.message, text, self.build_keyboard(menu_button, 1))
        await self.delete_messages(call_back.from_user.id, answer.message_id)
        await self.delete_history_basket(call_back.from_user.id, 'Корзина')

    async def record_data_order_by_xlsx(self, call_back: CallbackQuery):
        current_basket_dict = await self.execute.current_basket_for_xlsx(call_back.from_user.id)
        order = await self.save_order(call_back, current_basket_dict)
        number_order = order[0]
        order_path = order[1]
        await self.execute.record_order_xlsx(call_back.from_user.id, number_order, order_path)
        return number_order, order_path

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
        filepath = os.path.join(os.path.split(os.path.dirname(__file__))[0], f'data/basket/Заказ покупателя '
                                                                             f'{call_back.message.from_user.id} №'
                                                                             f'{number_order}.xlsx')
        new_book.save(filepath)
        new_book.close()
        return number_order, filepath

    async def answer_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    @staticmethod
    async def answer_message_by_basket(message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.answer(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def edit_message(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=self.format_text(text), parse_mode=ParseMode.HTML, reply_markup=keyboard)

    @staticmethod
    async def edit_message_by_basket(message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_text(text=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def answer_text(self, message: Message, text: str):
        return await message.answer(text=self.format_text(text), parse_mode=ParseMode.HTML,
                                    reply_to_message_id=message.message_id)

    async def edit_caption(self, message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_caption(caption=self.format_text(text), parse_mode=ParseMode.HTML,
                                          reply_markup=keyboard)

    @staticmethod
    async def edit_caption_by_basket(message: Message, text: str, keyboard: InlineKeyboardMarkup):
        return await message.edit_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    async def answer_photo(self, message: Message, photo: str, caption: str, keyboard: InlineKeyboardMarkup):
        try:
            return await message.answer_photo(photo=photo, caption=self.format_text(caption), parse_mode=ParseMode.HTML,
                                              reply_markup=keyboard)
        except TelegramBadRequest:
            photo = "https://www.rossvik.moscow/images/no_foto.png"
            return await message.answer_photo(photo=photo, caption=self.format_text(caption), parse_mode=ParseMode.HTML,
                                              reply_markup=keyboard)

    async def send_photo(self, message: Message, photo: str, text: str, amount_photo: int):
        media_group = MediaGroupBuilder(caption=text)
        if photo:
            arr_photo = photo.split()[:amount_photo]
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

    async def send_file(self, message: Message, document: str, text: str, keyboard: InlineKeyboardMarkup):
        if document != '':
            arr_content = document.split('///')
            return await message.answer_document(document=FSInputFile(arr_content[0]), caption=text,
                                                 parse_mode=ParseMode.HTML, reply_markup=keyboard)
        else:
            return await self.answer_message(message, text, keyboard)

    async def send_media(self, message: Message, media: list, server: bool = False):
        media_group = MediaGroupBuilder()
        for item in media:
            if server:
                if 'C:\\Python 3.11\\Мои проекты\\' in item:
                    path_file = os.path.join(os.path.split(os.path.dirname(__file__))[0],
                                             item.split('C:\\Python 3.11\\Мои проекты\\')[1])
                else:
                    path_file = item
            else:
                if 'C:\\Python 3.11\\Мои проекты\\' in item:
                    path_file = item
                else:
                    path_reverse = "\\".join(item.split("/"))
                    path_file = 'C:\\Python 3.11\\Мои проекты' + path_reverse
            file_input = FSInputFile(path_file)
            media_group.add_document(media=file_input, parse_mode=ParseMode.HTML)
        return await self.bot.send_media_group(chat_id=message.chat.id, media=media_group.build())

    async def create_keyboard_edit_caption(self, call_back: CallbackQuery, list_category: list, id_category: str):
        menu_button = {'back': '◀ 👈 Назад'}
        text = await self.execute.text_category(id_category)
        return await self.edit_caption(call_back.message, text,
                                       self.build_keyboard(self.assembling_category_dict(list_category), 1,
                                                           menu_button))

    async def create_keyboard_push_photo(self, call_back: CallbackQuery, list_category: list, id_category: str,
                                         name_logo: FSInputFile):
        menu_button = {'back': '◀ 👈 Назад'}
        text = await self.execute.text_category(id_category)
        answer = await self.bot.push_photo(call_back.message.chat.id,
                                           self.format_text(text),
                                           self.build_keyboard(self.assembling_category_dict(list_category),
                                                               1, menu_button),
                                           name_logo)
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
    def translit_rus_for_search(text_cross: str):
        text_list = list(text_cross)
        dict_letters = {'А': 'A', 'а': 'a', 'В': 'V', 'в': 'v', 'Е': 'E', 'е': 'e', 'К': 'K', 'к': 'k', 'М': 'M',
                        'м': 'm', 'Н': 'N', 'О': 'O', 'о': 'o', 'Р': 'R', 'р': 'r', 'С': 'C', 'с': 'c', 'Т': 'T',
                        'Х': 'X', 'х': 'x', 'У': 'Y', 'у': 'y', 'П': 'P', 'п': 'p'}
        for i in range(len(text_list)):
            if text_list[i] in dict_letters.keys():
                text_list[i] = dict_letters[text_list[i]]
        return ''.join(text_list)

    @staticmethod
    def get_arr_message_user(messages_user: str):
        arr_arr_message_user = messages_user.split('///')
        return arr_arr_message_user

    @staticmethod
    def get_arr_messages_user_for_record(arr_messages: list):
        string_record = '///'.join(arr_messages)
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
        await self.clean_timer(user)

    async def clean_timer(self, user: int):
        self.t.pop(user)
        await self.parent.start_for_timer(user)


class QueuesMedia:
    def __init__(self, parent):
        self.parent = parent
        self.queues = []
        self.info_media = None

    async def start(self, user_id: int, new_media: asyncio.Task):
        if len(self.queues) == 0:
            self.queues.append(new_media)
            start_info = await self.parent.execute.get_info_order(user_id)
            self.info_media = [start_info[8], start_info[9]]
            await self.start_task(user_id)
        else:
            self.queues.append(new_media)

    async def start_task(self, user_id: int):
        info = await self.queues[0]
        update_info = await self.parent.record_comment_and_content(info, self.info_media)
        self.info_media = update_info
        await self.delete_task_queues(user_id)

    async def delete_task_queues(self, user_id: int):
        self.queues.remove(self.queues[0])
        await self.restart_queues(user_id)

    async def restart_queues(self, user_id: int):
        if len(self.queues) != 0:
            await self.start_task(user_id)
        else:
            await self.parent.execute.record_order_comment_and_content(user_id, self.info_media[0], self.info_media[1])
            self.info_media = None
            await self.parent.change_head_message_by_media(user_id)


class QueuesMessage:
    def __init__(self):
        self.queues = []
        self.dict_name_task = {}
        self.queue_busy = False

    async def start(self, new_task: asyncio.Task):
        if new_task.get_name() in self.dict_name_task.keys():
            new_task.cancel()
        else:
            if len(self.queues) == 0:
                self.dict_name_task[new_task.get_name()] = new_task
                self.queues.append(new_task)
                await self.start_task()
            else:
                self.dict_name_task[new_task.get_name()] = new_task
                self.queues.append(new_task)

    async def start_task(self):
        self.queue_busy = await self.queues[0]
        if self.queue_busy:
            await self.delete_task_queues()
        else:
            print('Задача не выполнилась')

    async def delete_task_queues(self):
        self.dict_name_task.pop(self.queues[0].get_name())
        self.queues.remove(self.queues[0])
        await self.restart_queues()

    async def restart_queues(self):
        if len(self.queues) == 0:
            self.queue_busy = False
        else:
            await self.start_task()
