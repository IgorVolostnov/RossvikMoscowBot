import logging
import asyncio
import datetime
import aiosqlite
import requests
import re
import os
from dotenv import load_dotenv
from exception import send_message
from bs4 import BeautifulSoup
from urllib3.exceptions import NameResolutionError

logging.basicConfig(level=logging.INFO)
load_dotenv()


class UpdateBase:
    def __init__(self, url_xml):
        self.url_xml = url_xml
        self.timer_update_base = TimerUpdate(self, 3300)
        self.connect_string = os.path.join(os.path.split(os.path.dirname(__file__))[0], os.environ["CONNECTION"])
        self.response = None

    async def run(self):
        await self.timer_update_base.start()

    async def update_all(self):
        self.response = await self.request
        date_time_update = await self.get_date_update()
        await self.record_update_none('CATEGORY')
        await self.up_date_category(date_time_update)
        await self.delete_olds('CATEGORY')
        await self.show_category()
        await self.record_update_none('NOMENCLATURE')
        await self.up_date_nomenclature(date_time_update)
        await self.delete_olds('NOMENCLATURE')
        await self.show_nomenclature()

    async def get_date_update(self) -> str:
        date = '.'.join(self.response.find(name='yml_catalog')['date'].split('T')[0].split('-'))
        time_update = self.response.find(name='yml_catalog')['date'].split('T')[1].split('+')[0]
        return f"{date}_{time_update}"

    async def record_update_none(self, name_table: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_record_update_none(name_table)
        except Exception as e:
            await send_message('Ошибка запроса в методе record_update_none', os.environ["EMAIL"], str(e))

    async def execute_record_update_none(self, name_table: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE {name_table} SET " \
                         f"DATE_UPDATE = NULL "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def up_date_category(self, date: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_up_date_category(date)
        except Exception as e:
            await send_message('Ошибка запроса в методе up_date_category', os.environ["EMAIL"], str(e))

    async def execute_up_date_category(self, date: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            all_elements = await self.get_all_elements('category')
            for element in all_elements:
                sql_category = f"SELECT [KOD], [PARENT_ID], [NAME_CATEGORY], [DATE_UPDATE], [SORT_CATEGORY] " \
                               f"FROM [CATEGORY] " \
                               f"WHERE [KOD] = {self.quote(element.get('id'))} "
                await cursor.execute(sql_category)
                row_table = await cursor.fetchone()
                if row_table is None:
                    sql_record = f"INSERT INTO [CATEGORY] " \
                                 f"([KOD], [PARENT_ID], [NAME_CATEGORY], [DATE_UPDATE], [SORT_CATEGORY]) " \
                                 f"VALUES ('{element.get('id')}', " \
                                 f"'{element.get('parentId')}', " \
                                 f"'{element.text}', " \
                                 f"'{date}', " \
                                 f"'{1000}') "
                    await cursor.execute(sql_record)
                else:
                    sql_record = f"UPDATE [CATEGORY] SET " \
                                 f"[PARENT_ID] = '{element.get('parentId')}', " \
                                 f"[NAME_CATEGORY] = '{element.text}', " \
                                 f"[DATE_UPDATE] = '{date}' " \
                                 f"WHERE [KOD] = {self.quote(element.get('id'))} "
                    await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_olds(self, name_table: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_delete_olds(name_table)
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_olds', os.environ["EMAIL"], str(e))

    async def execute_delete_olds(self, name_table: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            await cursor.execute(f"DELETE FROM {name_table} WHERE DATE_UPDATE IS NULL ")
            await self.conn.commit()

    async def show_category(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_show_category()
        except Exception as e:
            await send_message('Ошибка запроса в методе show_category', os.environ["EMAIL"], str(e))

    async def execute_show_category(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT * FROM [CATEGORY] "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            print(f"Updated {len(row_table)} SKU categories {datetime.datetime.now()}")

    async def up_date_nomenclature(self, date: str):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_up_date_nomenclature(date)
        except Exception as e:
            await send_message('Ошибка запроса в методе up_date_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_up_date_nomenclature(self, date: str):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            all_elements = await self.get_all_elements('offer')
            for element in all_elements:
                article = await self.find_text_by_name_attribute(element, 'Артикул')
                name = await self.find_text_by_name_element(element, 'name')
                category_id = await self.find_text_by_name_element(element, 'categoryId')
                vendor = await self.find_text_by_name_element(element, 'vendor')
                description = await self.find_text_by_name_element(element, 'description')
                picture = await self.find_text_photo(element, 'picture')
                url = await self.find_text_by_name_element(element, 'url')
                amount = await self.find_text_by_name_attribute(element, 'Доступное количество')
                price = await self.find_text_by_name_element(element, 'price')
                dealer = await self.find_text_by_name_attribute(element, 'Дилерская Цена')
                if article == '':
                    article_change = self.translit_rus(re.sub(r"[^ \w]", '', name).upper())
                else:
                    article_change = self.translit_rus(re.sub(r"[^ \w]", '', article).upper())
                sql_nomenclature = f"SELECT [KOD], [CATEGORY_ID], [ARTICLE_CHANGE], [ARTICLE], [BRAND], [NAME], " \
                                   f"[DESCRIPTION], [PHOTO], [URL], [AVAILABILITY], [PRICE], [DEALER], [DATE_UPDATE] " \
                                   f"FROM [NOMENCLATURE] " \
                                   f"WHERE [KOD] = {self.quote(element.get('id'))} "
                await cursor.execute(sql_nomenclature)
                row_table = await cursor.fetchone()
                if row_table is None:
                    sql_record = f"INSERT INTO [NOMENCLATURE] ([KOD], [CATEGORY_ID], [ARTICLE_CHANGE], [ARTICLE], " \
                                 f"[BRAND], [NAME], [DISCOUNT], [DESCRIPTION], [SPECIFICATION], [PHOTO], [URL], " \
                                 f"[AVAILABILITY], [PRICE], [DEALER], [DISTRIBUTOR], [DATE_UPDATE], [VIEWS], " \
                                 f"[SORT_NOMENCLATURE], [CROSS]) " \
                                 f"VALUES ('{element.get('id')}', " \
                                 f"'{category_id}', " \
                                 f"'{article_change}', " \
                                 f"'{article}', " \
                                 f"'{vendor}', " \
                                 f"'{name}', " \
                                 f"'', " \
                                 f"'{description}', " \
                                 f"'', " \
                                 f"'{picture}', " \
                                 f"'{url}', " \
                                 f"'{amount}', " \
                                 f"'{price}', " \
                                 f"'{dealer}', " \
                                 f"'', " \
                                 f"'{date}', " \
                                 f"'', " \
                                 f"'{1000}', " \
                                 f"'') "
                    await cursor.execute(sql_record)
                else:
                    sql_record = f"UPDATE [NOMENCLATURE] SET " \
                                 f"[CATEGORY_ID] = '{category_id}', " \
                                 f"[ARTICLE_CHANGE] = '{article_change}', " \
                                 f"[ARTICLE] = '{article}', " \
                                 f"[BRAND] = '{vendor}', " \
                                 f"[NAME] = '{name}', " \
                                 f"[DESCRIPTION] = '{description}', " \
                                 f"[PHOTO] = '{picture}', " \
                                 f"[URL] = '{url}', " \
                                 f"[AVAILABILITY] = '{amount}', " \
                                 f"[PRICE] = '{price}', " \
                                 f"[DEALER] = '{dealer}', " \
                                 f"[DATE_UPDATE] = '{date}' " \
                                 f"WHERE [KOD] = {self.quote(element.get('id'))} "
                    await cursor.execute(sql_record)
            await self.conn.commit()

    async def show_nomenclature(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_show_nomenclature()
        except Exception as e:
            await send_message('Ошибка запроса в методе show_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_show_nomenclature(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_nomenclature = f"SELECT * FROM [NOMENCLATURE] "
            await cursor.execute(sql_nomenclature)
            row_table = await cursor.fetchall()
            print(f"Updated {len(row_table)} SKU nomenclatures {datetime.datetime.now()}")

    @property
    async def request(self):
        try:
            response = requests.get(self.url_xml)
            if response.status_code != 200:
                print('Не получен ответ по ссылке xml-файла')
                return None
            else:
                return BeautifulSoup(response.content, "xml")
        except ConnectionError:
            return None
        except NameResolutionError:
            return None

    async def get_all_elements(self, name_element):
        return self.response.find_all(name=name_element)

    @staticmethod
    async def find_text_by_name_element(element, name_element):
        if element.find(name_element) is None:
            text = 'Нет подробной информации'
        else:
            text = element.find(name_element).text
        return text

    @staticmethod
    async def find_text_by_name_attribute(element, name_attribute):
        if element.find(attrs={'name': name_attribute}) is None:
            text = ''
        else:
            text = element.find(attrs={'name': name_attribute}).text
        return text

    @staticmethod
    async def find_text_by_id_category(element, id_category):
        if element.find(attrs={'id': id_category}) is None:
            text = ''
        else:
            text = element.find(attrs={'id': id_category}).text
        return text

    @staticmethod
    async def find_text_photo(element, name_attribute):
        arr_picture = []
        for photo in element.find_all(name_attribute):
            arr_picture.append(photo.text)
        return ' '.join(arr_picture)

    @staticmethod
    def translit_rus(text_cross):
        text_list = list(text_cross)
        dict_letters = {'А': 'A', 'а': 'a', 'В': 'B', 'Е': 'E', 'е': 'e', 'К': 'K', 'к': 'k', 'М': 'M', 'Н': 'H',
                        'О': 'O', 'о': 'o', 'Р': 'P', 'р': 'p', 'С': 'C', 'с': 'c', 'Т': 'T', 'Х': 'X', 'х': 'x'}
        for i in range(len(text_list)):
            if text_list[i] in dict_letters.keys():
                text_list[i] = dict_letters[text_list[i]]
        return ''.join(text_list)

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"


class TimerUpdate:
    def __init__(self, parent, second: int):
        self.parent = parent
        self._clean_time = second
        self.task = {}

    async def start(self):
        if 'current_update' in self.task.keys():
            self.task['current_update'].cancel()
            self.task.pop('current_update')
            self.task['current_update'] = asyncio.create_task(self.update_base())
            await self.task['current_update']
        else:
            self.task['current_update'] = asyncio.create_task(self.update_base())
            await self.task['current_update']

    async def update_base(self):
        await asyncio.sleep(self._clean_time)
        await self.parent.update_all()
        await self.clean_timer()

    async def clean_timer(self):
        self.task.pop('current_update')
        await self.start()
