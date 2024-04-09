from execute import Execute
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
        self.delivery = {'pickup': 'Самовывоз',
                         'delivery': 'Доставка'}
        self.kind_pickup = {'record_answer_shop': 'Москва, Хачатуряна, 8 корпус 3 (Магазин)',
                            'record_answer_storage': 'Мытищи, 1-ая Новая, 57 (Склад)'}
        self.kind_delivery = {'record_answer_moscow': 'В пределах МКАД',
                              'record_answer_pek': 'ТК ПЭК',
                              'record_answer_dl': 'ТК Деловые Линии',
                              'record_answer_mt': 'ТК Мейджик Транс',
                              'record_answer_cdek': 'ТК СДЭК'}
        self.execute = Execute()

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

    async def get_calculater_keyboard(self, id_user: int):
        arr_basket = await self.execute.current_basket(id_user)
        if arr_basket is None:
            self.calculater['basket'] = f"Корзина 🛒(0 шт. на 0 ₽)"
        else:
            sum_item = 0
            for item in arr_basket:
                arr_item = item.split('///')
                sum_item += float(arr_item[2])
            self.calculater['basket'] = f"Корзина 🛒({len(arr_basket)} шт. на {self.format_price(float(sum_item))})"
        return self.calculater

    async def get_description_button(self, id_user: int):
        arr_basket = await self.execute.current_basket(id_user)
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
