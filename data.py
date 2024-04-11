from execute import Execute
from operator import itemgetter


class DATA:
    def __init__(self):
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
                      ['702', 'Запчасти 🧩⚙️', 100],
                      ['1101', 'Садовый инвентарь 👩‍🌾', 100],
                      ['738', 'Электроинструмент 🔋', 100],
                      ['1100', 'Автотовары 🍱', 100],
                      ['688', 'Мебель для автосервиса 🗄️', 100],
                      ['1095', 'Вытяжка отработанных газов ♨', 100],
                      ['660', 'Сход/развалы 🔩📐', 100],
                      ['663', 'Мойки деталей 🛁', 100],
                      ['692', 'Экспресс-сервис 🚅🤝🏻', 100]]
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

    async def get_first_keyboard(self, id_user: int):
        basket = await self.get_basket(id_user)
        first_keyboard = {'news': 'Новости 📣🌐💬', 'orders': 'Мои Заказы 🗃️🛒', 'basket': basket['basket'],
                          'catalog': 'Каталог🛒🧾👀'}
        return first_keyboard

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
    def get_nomenclature(self):
        dict_nomenclature = {}
        for item in range(4000, 30000):
            dict_nomenclature[str(item)] = str(item)
        return dict_nomenclature

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

    async def get_calculater(self, id_user: int, id_nomenclature: str):
        calculater = {f'{id_nomenclature}///1': '1⃣', f'{id_nomenclature}///2': '2⃣', f'{id_nomenclature}///3': '3⃣',
                      f'{id_nomenclature}///4': '4⃣', f'{id_nomenclature}///5': '5⃣', f'{id_nomenclature}///6': '6⃣',
                      f'{id_nomenclature}///7': '7⃣', f'{id_nomenclature}///8': '8️⃣', f'{id_nomenclature}///9': '9⃣',
                      f'{id_nomenclature}minus': '➖', f'{id_nomenclature}///0': '0️⃣',
                      f'{id_nomenclature}plus': '➕',  f'{id_nomenclature}back_add': '◀👈 Назад',
                      f'{id_nomenclature}delete': '⌫', f'{id_nomenclature}done': 'Готово ✅🗑️',
                      'basket': f'Корзина 🛒(0 шт на 0 руб.)'}
        arr_basket = await self.execute.current_basket(id_user)
        if arr_basket is None:
            calculater['basket'] = f"Корзина 🛒(0 шт. на 0 ₽)"
        else:
            sum_item = 0
            for item in arr_basket:
                arr_item = item.split('///')
                sum_item += float(arr_item[2])
            calculater['basket'] = f"Корзина 🛒({len(arr_basket)} шт. на {self.format_price(float(sum_item))})"
        return calculater

    @property
    def get_button_calculater(self):
        dict_button_calculater = {}
        for item in range(10):
            for id_nomenclature in range(4000, 30000):
                dict_button_calculater[f'{str(id_nomenclature)}///{str(item)}'] = str(item)
        return dict_button_calculater

    @staticmethod
    def get_dict_value(value: str, start: int, finish: int):
        dict_value = {}
        for item in range(start, finish):
            dict_value[f'{str(item)}{value}'] = str(item)
        return dict_value

    async def get_basket(self, id_user: int):
        basket = {}
        arr_basket = await self.execute.current_basket(id_user)
        if arr_basket is None:
            basket['basket'] = f"Корзина 🛒(0 шт. на 0 ₽)"
        else:
            sum_item = 0
            for item in arr_basket:
                arr_item = item.split('///')
                sum_item += float(arr_item[2])
            basket['basket'] = f"Корзина 🛒({len(arr_basket)} шт. на {self.format_price(float(sum_item))})"
        return basket

    @staticmethod
    def format_price(item: float):
        return '{0:,} ₽'.format(item).replace(',', ' ')

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"
