import logging
import asyncio
import datetime
import time
import aiosqlite
import requests
import re
import os
from prettytable import PrettyTable
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
        await self.record_update_none_category()
        await self.up_date_base_category(date_time_update)
        await self.delete_olds_category()
        await self.show_category()
        await self.record_update_none_nomenclature()
        await self.up_date_base_nomenclature(date_time_update)
        await self.delete_olds_nomenclature()
        await self.show_nomenclature()

    async def get_date_update(self) -> str:
        date = '.'.join(self.response.find(name='yml_catalog')['date'].split('T')[0].split('-'))
        time_update = self.response.find(name='yml_catalog')['date'].split('T')[1].split('+')[0]
        return f"{date}_{time_update}"

    async def record_update_none_category(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_record_update_none_category()
        except Exception as e:
            await send_message('Ошибка запроса в методе record_update_none_category', os.environ["EMAIL"], str(e))

    async def execute_record_update_none_category(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE CATEGORY SET DATE_UPDATE_CATEGORY = NULL "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def up_date_base_category(self, date: str):
        dict_category = await self.up_date_dict_category(date)
        for key, item in dict_category.items():
            await self.up_date_category([key, item[0], item[1], item[2], item[3]])

    async def up_date_dict_category(self, date: str):
        all_elements = await self.get_all_elements('category')
        list_category = await self.select_all_category()
        dict_category = await self.get_dict_category(list_category)
        for element in all_elements:
            id_element = element.get('id')
            try:
                sort_element = dict_category[id_element][3]
                dict_category[id_element] = [element.get('parentId'), element.text, date, sort_element]
            except KeyError:
                # print(f'Код {id_element} не нашли в базе')
                dict_category[id_element] = [element.get('parentId'), element.text, date, 100]
        print(len(dict_category))
        return dict_category

    @staticmethod
    async def get_dict_category(list_category: list) -> dict:
        dict_category = {}
        for item in list_category:
            dict_category[item[0]] = [item[1], item[2], item[3], item[4]]
        return dict_category

    async def select_all_category(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_select_all_category()
        except Exception as e:
            await send_message('Ошибка запроса в методе select_all_category', os.environ["EMAIL"], str(e))

    async def execute_select_all_category(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT * FROM CATEGORY "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            return row_table

    async def up_date_category(self, data: list):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_up_date_category(data)
        except Exception as e:
            await send_message('Ошибка запроса в методе up_date_category', os.environ["EMAIL"], str(e))

    async def execute_up_date_category(self, data: list):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"INSERT INTO CATEGORY " \
                         f"(ID, PARENT_ID, NAME_CATEGORY, DATE_UPDATE_CATEGORY, SORT_CATEGORY, LOGO_CATEGORY) " \
                         f"VALUES('{data[0]}', '{data[1]}', '{data[2]}', '{data[3]}', '{data[4]}', '') " \
                         f"ON CONFLICT (ID) DO UPDATE SET " \
                         f"PARENT_ID = '{data[1]}', " \
                         f"NAME_CATEGORY = '{data[2]}', " \
                         f"DATE_UPDATE_CATEGORY = '{data[3]}' " \
                         f"WHERE ID = {data[0]} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_olds_category(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_delete_olds_category()
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_olds_category', os.environ["EMAIL"], str(e))

    async def execute_delete_olds_category(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            await cursor.execute(f"DELETE FROM CATEGORY WHERE DATE_UPDATE_CATEGORY IS NULL ")
            await self.conn.commit()

    async def show_category(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_show_category()
        except Exception as e:
            await send_message('Ошибка запроса в методе show_category', os.environ["EMAIL"], str(e))

    async def execute_show_category(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT * FROM CATEGORY "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            # my_table = PrettyTable()
            # my_table.field_names = ["ID", "PARENT_ID", "NAME_CATEGORY", "DATE_UPDATE_CATEGORY", "SORT_CATEGORY",
            #                         "LOGO_CATEGORY"]
            # for item in row_table:
            #     my_table.add_row([item[0], item[1], item[2], item[3], item[4], item[5]])
            # print(my_table)
            print(f"Updated {len(row_table)} SKU categories {datetime.datetime.now()}")

    async def record_update_none_nomenclature(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_record_update_none_nomenclature()
        except Exception as e:
            await send_message('Ошибка запроса в методе record_update_none_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_record_update_none_nomenclature(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"UPDATE NOMENCLATURE SET " \
                         f"DATE_UPDATE_NOMENCLATURE = NULL "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def up_date_base_nomenclature(self, date: str):
        dict_nomenclature = await self.up_date_dict_nomenclature(date)
        for key, item in dict_nomenclature.items():
            await self.up_date_nomenclature([key, item[0], item[1], item[2], item[3], item[4], item[5], item[6],
                                             item[7], item[8], item[9], item[10], item[11], item[12], item[13],
                                             item[14], item[15], item[16]])

    async def up_date_dict_nomenclature(self, date: str):
        all_elements = await self.get_all_elements('offer')
        list_nomenclature = await self.select_all_nomenclature()
        dict_nomenclature = await self.get_dict_nomenclature(list_nomenclature)
        for element in all_elements:
            id_element = element.get('id')
            category_id = await self.find_text_by_name_element(element, 'categoryId')
            article = await self.find_text_by_name_attribute(element, 'Артикул')
            name = await self.find_text_by_name_element(element, 'name')
            if article == '':
                article_change = self.translit_rus(re.sub(r"[^ \w]", '', name).upper())
            else:
                article_change = self.translit_rus(re.sub(r"[^ \w]", '', article).upper())
            vendor = await self.find_text_by_name_element(element, 'vendor')
            description = await self.find_text_by_name_element(element, 'description')
            picture = await self.find_text_photo(element, 'picture')
            url = await self.find_text_by_name_element(element, 'url')
            amount = await self.find_text_by_name_attribute(element, 'Доступное количество')
            if float(amount) < 0 or amount == '':
                amount = 0
            price = await self.find_text_by_name_element(element, 'price')
            dealer = await self.find_text_by_name_attribute(element, 'Дилерская Цена')
            if dealer == '':
                dealer = 0
            try:
                sort_element = dict_nomenclature[id_element][16]
                discount = dict_nomenclature[id_element][5]
                specification = dict_nomenclature[id_element][7]
                distributor = dict_nomenclature[id_element][13]
                views = dict_nomenclature[id_element][15]
                dict_nomenclature[id_element] = [category_id, article_change, article, vendor, name, discount,
                                                 description, specification, picture, url, float(amount), float(price),
                                                 float(dealer), distributor, date, views, sort_element]
            except KeyError:
                # print(f'Код {id_element} не нашли в базе')
                dict_nomenclature[id_element] = [category_id, article_change, article, vendor, name, 0,
                                                 description, '', picture, url, float(amount), float(price),
                                                 float(dealer), 0, date, 0, 1000]
        print(len(dict_nomenclature))
        return dict_nomenclature

    @staticmethod
    async def get_dict_nomenclature(list_nomenclature: list) -> dict:
        dict_nomenclature = {}
        for item in list_nomenclature:
            dict_nomenclature[item[0]] = [item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8],
                                          item[9], item[10], item[11], item[12], item[13], item[14], item[15],
                                          item[16], item[17]]
        return dict_nomenclature

    async def select_all_nomenclature(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                return await self.execute_select_all_nomenclature()
        except Exception as e:
            await send_message('Ошибка запроса в методе select_all_category', os.environ["EMAIL"], str(e))

    async def execute_select_all_nomenclature(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT * FROM NOMENCLATURE "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            return row_table

    async def up_date_nomenclature(self, data: list):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_up_date_nomenclature(data)
        except Exception as e:
            await send_message('Ошибка запроса в методе up_date_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_up_date_nomenclature(self, data: list):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_record = f"INSERT INTO NOMENCLATURE " \
                         f"(ID, CATEGORY_ID, ARTICLE_CHANGE, ARTICLE, BRAND, NAME_NOMENCLATURE, " \
                         f"DISCOUNT_NOMENCLATURE, DESCRIPTION_NOMENCLATURE, SPECIFICATION_NOMENCLATURE, " \
                         f"PHOTO_NOMENCLATURE, URL_NOMENCLATURE, AVAILABILITY_NOMENCLATURE, PRICE_NOMENCLATURE, " \
                         f"DEALER_NOMENCLATURE, DISTRIBUTOR_NOMENCLATURE, DATE_UPDATE_NOMENCLATURE, " \
                         f"VIEWS_NOMENCLATURE, SORT_NOMENCLATURE) " \
                         f"VALUES('{data[0]}', '{data[1]}', '{data[2]}', '{data[3]}', '{data[4]}', '{data[5]}', " \
                         f"'{data[6]}', '{data[7]}', '{data[8]}', '{data[9]}', '{data[10]}', '{data[11]}', " \
                         f"'{data[12]}', '{data[13]}', '{data[14]}', '{data[15]}', '{data[16]}', '{data[17]}') " \
                         f"ON CONFLICT (ID) DO UPDATE SET " \
                         f"CATEGORY_ID = '{data[1]}', " \
                         f"ARTICLE_CHANGE = '{data[2]}', " \
                         f"ARTICLE = '{data[3]}', " \
                         f"BRAND = '{data[4]}', " \
                         f"NAME_NOMENCLATURE = '{data[5]}', " \
                         f"DISCOUNT_NOMENCLATURE = '{data[6]}', " \
                         f"DESCRIPTION_NOMENCLATURE = '{data[7]}', " \
                         f"SPECIFICATION_NOMENCLATURE = '{data[8]}', " \
                         f"PHOTO_NOMENCLATURE = '{data[9]}', " \
                         f"URL_NOMENCLATURE = '{data[10]}', " \
                         f"AVAILABILITY_NOMENCLATURE = '{data[11]}', " \
                         f"PRICE_NOMENCLATURE = '{data[12]}', " \
                         f"DEALER_NOMENCLATURE = '{data[13]}', " \
                         f"DISTRIBUTOR_NOMENCLATURE = '{data[14]}', " \
                         f"DATE_UPDATE_NOMENCLATURE = '{data[15]}', " \
                         f"VIEWS_NOMENCLATURE = '{data[16]}', " \
                         f"SORT_NOMENCLATURE = '{data[17]}' " \
                         f"WHERE ID = {data[0]} "
            await cursor.execute(sql_record)
            await self.conn.commit()

    async def delete_olds_nomenclature(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_delete_olds_nomenclature()
        except Exception as e:
            await send_message('Ошибка запроса в методе delete_olds_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_delete_olds_nomenclature(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            await cursor.execute(f"DELETE FROM NOMENCLATURE WHERE DATE_UPDATE_NOMENCLATURE IS NULL ")
            await self.conn.commit()

    async def show_nomenclature(self):
        try:
            async with aiosqlite.connect(self.connect_string) as self.conn:
                await self.execute_show_nomenclature()
        except Exception as e:
            await send_message('Ошибка запроса в методе show_nomenclature', os.environ["EMAIL"], str(e))

    async def execute_show_nomenclature(self):
        async with self.conn.execute('PRAGMA journal_mode=wal') as cursor:
            sql_category = f"SELECT * FROM NOMENCLATURE "
            await cursor.execute(sql_category)
            row_table = await cursor.fetchall()
            # my_table = PrettyTable()
            # my_table.field_names = ["ID", "CATEGORY_ID", "ARTICLE_CHANGE", "ARTICLE", "BRAND", "NAME_NOMENCLATURE",
            #                         "DISCOUNT_NOMENCLATURE", "DESCRIPTION_NOMENCLATURE",
            #                         "SPECIFICATION_NOMENCLATURE", "PHOTO_NOMENCLATURE", "URL_NOMENCLATURE",
            #                         "AVAILABILITY_NOMENCLATURE", "PRICE_NOMENCLATURE", "DEALER_NOMENCLATURE",
            #                         "DISTRIBUTOR_NOMENCLATURE", "DATE_UPDATE_NOMENCLATURE", "VIEWS_NOMENCLATURE",
            #                         "SORT_NOMENCLATURE"]
            # for item in row_table:
            #     my_table.add_row([item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8],
            #                       item[9], item[10], item[11], item[12], item[13], item[14], item[15], item[16],
            #                       item[17]])
            # print(my_table)
            print(f"Updated {len(row_table)} SKU categories {datetime.datetime.now()}")

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
        start_time = time.time()
        await self.parent.update_all()
        print("--- %s seconds ---" % (time.time() - start_time))
        await self.clean_timer()

    async def clean_timer(self):
        self.task.pop('current_update')
        await self.start()


# up_data = UpdateBase(os.environ["XML_DATA"])
# asyncio.run(up_data.run())
