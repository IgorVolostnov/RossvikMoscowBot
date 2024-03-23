import sqlite3
import os
from operator import itemgetter


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