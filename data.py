from execute import Execute
from operator import itemgetter
from language import Language


class DATA:
    def __init__(self):
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
        self.language_data = Language()

    async def get_first_keyboard(self, id_user: int, status_user: str, user_language: str) -> dict:
        text_basket = await self.get_basket(id_user)
        amount_order = await self.execute.get_amount_order(id_user)
        language_first_keyboard = {'russian': {'text_news': 'Новости 📣🌐💬',
                                               'text_orders': f'Мои Заказы 🗃️ (Новых заказов: {str(amount_order)})',
                                               'text_basket': text_basket['basket'][user_language],
                                               'text_catalog': 'Каталог🧾👀',
                                               'text_update': 'Обновить сообщения💬',
                                               'text_add_status': 'Присвоить статус😎'},
                                   'azerbaijani': {'text_news': 'Xəbərlər 📣🌐💬',
                                                   'text_orders': f'Sifarişlərim 🗃️ (Yeni sifarişlər: '
                                                                  f'{str(amount_order)})',
                                                   'text_basket': text_basket['basket'][user_language],
                                                   'text_catalog': 'Kataloq🧾👀',
                                                   'text_update': 'Mesajları yeniləyin💬',
                                                   'text_add_status': 'Status verin😎'}
                                   }
        if status_user == 'creator':
            first_keyboard = {'https://t.me/rossvik_moscow': language_first_keyboard[user_language]['text_news'],
                              'orders': language_first_keyboard[user_language]['text_orders'],
                              'basket': language_first_keyboard[user_language]['text_basket'],
                              'catalog': language_first_keyboard[user_language]['text_catalog'],
                              'update': language_first_keyboard[user_language]['text_update'],
                              'add_status': language_first_keyboard[user_language]['text_add_status']}
        elif status_user == 'admin':
            first_keyboard = {'https://t.me/rossvik_moscow': language_first_keyboard[user_language]['text_news'],
                              'orders': language_first_keyboard[user_language]['text_orders'],
                              'basket': language_first_keyboard[user_language]['text_basket'],
                              'catalog': language_first_keyboard[user_language]['text_catalog'],
                              'add_status': language_first_keyboard[user_language]['text_add_status']}
        else:
            first_keyboard = {'https://t.me/rossvik_moscow': language_first_keyboard[user_language]['text_news'],
                              'orders': language_first_keyboard[user_language]['text_orders'],
                              'basket': language_first_keyboard[user_language]['text_basket'],
                              'catalog': language_first_keyboard[user_language]['text_catalog']}
        return first_keyboard

    @staticmethod
    async def get_info_help(language_user: str) -> str:
        space = '\n'
        language_help = {'russian': {'first_str': 'Вы можете воспользоваться быстрой навигацией, отправляя следующие '
                                                  'команды:',
                                     'menu_str': 'главное меню',
                                     'catalog_str': 'каталог товара',
                                     'news_str': 'новости',
                                     'basket_str': 'корзина',
                                     'order_str': 'история заказов',
                                     'main_str': f'Поиск товара:{space}{space}При отправке боту сообщения происходит '
                                                 f'поиск товара в каталоге по содержимому сообщения, разделенному '
                                                 f'пробелами. Можно указывать не только слова, но и символы, '
                                                 f'которые содержатся в наименовании товара.{space}Чтобы понять, '
                                                 f'как это работает, попробуйте отправить боту сообщение:{space}'
                                                 f'пласт вст{space}{space}УВЕДОМЛЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ: '
                                                 f'Все данные, полученные в процессе взаимодействия между Ботом и '
                                                 f'Пользователем: фото, видео, текстовая информация, а также любые '
                                                 f'отправленные документы, которые содержат конфиденциальную '
                                                 f'информацию не подлежат использованию, копированию, распространению,'
                                                 f' а также осуществлению любых других действий на их основе.'},
                         'azerbaijani': {'first_str': 'aşağıdakıları göndərərək sürətli naviqasiyadan faydalana '
                                                      'bilərsiniz komandalar:',
                                         'menu_str': 'əsas menyu',
                                         'catalog_str': 'məhsul kataloqu',
                                         'news_str': 'xəbərlər',
                                         'basket_str': 'səbət',
                                         'order_str': 'sifariş tarixi',
                                         'main_str': f'məhsul axtarışı:{space}{space}Bota mesaj göndərərkən '
                                                     f'bölünmüş mesaj məzmununa görə Kataloqda məhsul axtarın '
                                                     f'boşluqlar. Yalnız sözləri deyil, simvolları da göstərə '
                                                     f'bilərsiniz, malların adında olanlar.{space}anlamaq üçün, '
                                                     f'necə işləyir, Bota mesaj göndərməyə çalışın:{space}'
                                                     f'пласт вст{space}{space}Məxfilik Bildirişi: '
                                                     f'bot və arasındakı qarşılıqlı əlaqə prosesində əldə edilən bütün '
                                                     f'məlumatlar istifadəçi: foto, video, mətn məlumat, eləcə də hər '
                                                     f'hansı məxfi olan sənədlər göndərildi məlumat istifadə edilə '
                                                     f'bilməz, kopyalana bilməz, paylaşıla bilməz, və onlara əsaslanan '
                                                     f'hər hansı digər hərəkətlərin həyata keçirilməsi.'}
                         }
        info = f"{language_help[language_user]['first_str']}{space}{space}" \
               f"/start - {language_help[language_user]['menu_str']}{space}" \
               f"/catalog - {language_help[language_user]['catalog_str']}{space}" \
               f"/news - {language_help[language_user]['news_str']}{space}" \
               f"/basket - {language_help[language_user]['basket_str']}{space}" \
               f"/order - {language_help[language_user]['order_str']}{space}" \
               f"{space}{language_help[language_user]['main_str']}"
        return info

    @staticmethod
    async def get_prices(language_user: str) -> dict:
        language_price = {'russian': {'repair_materials': 'Шиноремонтные материалы ✂⚒',
                                      'valves': 'Вентили 🔌',
                                      'repair_spikes': 'Ремонтные шипы ‍🌵',
                                      'balancing_weights': 'Грузики балансировочные ⚖',
                                      'tire_fitting_equipment': 'Шиномонтажное оборудование 🚗🔧',
                                      'lifting_equipment': 'Подъемное оборудование ⛓',
                                      'hand_tool': 'Ручной инструмент 🔧',
                                      'special_tools': 'Специнструмент 🛠',
                                      'refueling_air_conditioners': 'Заправки кондиционеров ❄',
                                      'compressors': 'Компрессоры ⛽',
                                      'pneumatic_tool': 'Пневмоинструмент 🎣',
                                      'pneumolines': 'Пневмолинии 💨💧',
                                      'consumables_car_service': 'Расходные материалы для автосервиса 📜🚗',
                                      'washing_cleaning_equipment': 'Моечно-уборочное оборудование 🧹',
                                      'auto_chemistry': 'АвтоХимия ☣⚗',
                                      'garage_equipment': 'Гаражное оборудование 👨🏾‍🔧',
                                      'diagnostic_equipment': 'Диагностическое оборудование 🕵️‍♀',
                                      'oil_changing_equipment': 'Маслосменное оборудование 💦🛢️',
                                      'spare_parts': 'Запчасти 🧩⚙️',
                                      'garden_equipment': 'Садовая техника 👩‍🌾',
                                      'power_tool': 'Электроинструмент 🔋',
                                      'automotive_products': 'Автотовары 🍱',
                                      'car_service_furniture': 'Мебель для автосервиса 🗄️',
                                      'exhaust_gas_extraction': 'Вытяжка отработанных газов ♨',
                                      'convergence_collapse': 'Сход/развалы 🔩📐',
                                      'washing_parts': 'Мойки деталей 🛁',
                                      'express_service': 'Экспресс-сервис 🚅🤝🏻',
                                      'chargers': 'Зарядные и пуско-зарядные устройства ⚡',
                                      'cutting_tool': 'Режущий инструмент 🔪'
                                      },
                          'azerbaijani': {'repair_materials': 'Şin təmiri materialları ✂⚒',
                                          'valves': 'Vana 🔌',
                                          'repair_spikes': 'Təmir tırmanıştır ‍🌵',
                                          'balancing_weights': 'Balans çəkiləri ⚖',
                                          'tire_fitting_equipment': 'Şin montaj avadanlığı 🚗🔧',
                                          'lifting_equipment': 'Qaldırıcı avadanlıq ⛓',
                                          'hand_tool': 'Əl aləti 🔧',
                                          'special_tools': 'Xüsusi alət 🛠',
                                          'refueling_air_conditioners': 'Kondisionerlərin doldurulması ❄',
                                          'compressors': 'Kompressorlar ⛽',
                                          'pneumatic_tool': 'Pnevmatik alət 🎣',
                                          'pneumolines': 'Pnevmoliniya 💨💧',
                                          'consumables_car_service': 'Avtomobil xidməti üçün istehlak materialları 📜🚗',
                                          'washing_cleaning_equipment': 'Yuyucu və təmizləyici avadanlıq 🧹',
                                          'auto_chemistry': 'Avtokimya ☣⚗',
                                          'garage_equipment': 'Qaraj avadanlığı 👨🏾‍🔧',
                                          'diagnostic_equipment': 'Diaqnostik avadanlıq 🕵️‍♀',
                                          'oil_changing_equipment': 'Yağ dəyişdirmə avadanlığı 💦🛢️',
                                          'spare_parts': 'Ehtiyat hissələri 🧩⚙️',
                                          'garden_equipment': 'Bağ texnikası 👩‍🌾',
                                          'power_tool': 'Elektrik aləti 🔋',
                                          'automotive_products': 'Avtovağzal 🍱',
                                          'car_service_furniture': 'Avtomobil xidməti üçün mebel 🗄️',
                                          'exhaust_gas_extraction': 'İşlənmiş qaz ekstraktı ♨',
                                          'convergence_collapse': 'Yıxılma/Kamber 🔩📐',
                                          'washing_parts': 'Yuma hissələri 🛁',
                                          'express_service': 'Ekspress xidmət 🚅🤝🏻',
                                          'chargers': 'Şarj cihazları və şarj cihazları ⚡',
                                          'cutting_tool': 'Kəsmə aləti 🔪'}
                          }
        price = [['506', language_price[language_user]['repair_materials'], 100],
                 ['507', language_price[language_user]['valves'], 100],
                 ['556', language_price[language_user]['repair_spikes'], 100],
                 ['658', language_price[language_user]['balancing_weights'], 100],
                 ['552', language_price[language_user]['tire_fitting_equipment'], 100],
                 ['600', language_price[language_user]['lifting_equipment'], 100],
                 ['547', language_price[language_user]['hand_tool'], 100],
                 ['608', language_price[language_user]['special_tools'], 100],
                 ['726', language_price[language_user]['refueling_air_conditioners'], 100],
                 ['549', language_price[language_user]['compressors'], 100],
                 ['597', language_price[language_user]['pneumatic_tool'], 100],
                 ['707', language_price[language_user]['pneumolines'], 100],
                 ['623', language_price[language_user]['consumables_car_service'], 100],
                 ['946', language_price[language_user]['washing_cleaning_equipment'], 100],
                 ['493', language_price[language_user]['auto_chemistry'], 100],
                 ['580', language_price[language_user]['garage_equipment'], 100],
                 ['593', language_price[language_user]['diagnostic_equipment'], 100],
                 ['603', language_price[language_user]['oil_changing_equipment'], 100],
                 ['702', language_price[language_user]['spare_parts'], 100],
                 ['1101', language_price[language_user]['garden_equipment'], 100],
                 ['738', language_price[language_user]['power_tool'], 100],
                 ['1100', language_price[language_user]['automotive_products'], 100],
                 ['688', language_price[language_user]['car_service_furniture'], 100],
                 ['1095', language_price[language_user]['exhaust_gas_extraction'], 100],
                 ['660', language_price[language_user]['convergence_collapse'], 100],
                 ['663', language_price[language_user]['washing_parts'], 100],
                 ['692', language_price[language_user]['express_service'], 100],
                 ['942', language_price[language_user]['chargers'], 100],
                 ['1237', language_price[language_user]['cutting_tool'], 100]]
        dict_price = {}
        for item in sorted(price, key=itemgetter(2), reverse=False):
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
    def get_dealer_price_remove(self):
        dict_dealer_price_remove = {}
        for item in range(4000, 30000):
            dict_dealer_price_remove[f'{str(item)}remove_dealer_price'] = str(item)
        return dict_dealer_price_remove

    @property
    def get_dealer_price_show(self):
        dict_dealer_price_show = {}
        for item in range(4000, 30000):
            dict_dealer_price_show[f'{str(item)}show_dealer_price'] = str(item)
        return dict_dealer_price_show

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
    def get_pages_basket(self):
        dict_pages_basket = {}
        for item in range(100):
            dict_pages_basket['Корзина_Стр.' + str(item)] = str(item)
        return dict_pages_basket

    async def get_calculater(self, id_user: int, id_nomenclature: str):
        calculater = {f'{id_nomenclature}///1': '1⃣', f'{id_nomenclature}///2': '2⃣', f'{id_nomenclature}///3': '3⃣',
                      f'{id_nomenclature}///4': '4⃣', f'{id_nomenclature}///5': '5⃣', f'{id_nomenclature}///6': '6⃣',
                      f'{id_nomenclature}///7': '7⃣', f'{id_nomenclature}///8': '8️⃣', f'{id_nomenclature}///9': '9⃣',
                      f'{id_nomenclature}minus': '➖', f'{id_nomenclature}///0': '0️⃣',
                      f'{id_nomenclature}plus': '➕',  f'{id_nomenclature}back_add': '◀👈 Назад',
                      f'{id_nomenclature}delete': '⌫', f'{id_nomenclature}done': 'Готово ✅🗑️',
                      'basket': f'Корзина 🛒(0 шт на 0 руб.)'}
        amount = await self.execute.current_amount_basket(id_user)
        sum_basket = await self.execute.current_sum_basket(id_user)
        if amount is None:
            calculater['basket'] = f"Корзина 🛒(0 шт. на 0 ₽)"
        else:
            calculater['basket'] = f"Корзина 🛒({int(amount)} шт. на {self.format_price(float(sum_basket))})"
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
        amount = await self.execute.current_amount_basket(id_user)
        sum_basket = await self.execute.current_sum_basket(id_user)
        if amount is None:
            basket['basket'] = {'russian': 'Корзина 🛒(0 шт. на 0 ₽)',
                                'armenian': 'Զամբյուղ 🛒(0 հատ 0 ₽)',
                                'azerbaijani': 'Səbət (0 ədəd 0 ₽)',
                                'english': 'Basket 🛒(0 pieces per 0 ₽)',
                                'georgian': 'კალათა 🛒(0 ცალი 0 ₽)',
                                'kazakh': 'Себет 🛒(0 дана 0 ₽)',
                                'kyrgyz': 'Себет 🛒(0 даана 0 ₽)',
                                'mongolian': 'Сагс 🛒(0 ширхэг тутамд 0 ₽)',
                                'tajik': 'Сабад 🛒(0 дона ба 0 ₽)',
                                'uzbek': 'Savat 🛒(0 dona 0 ₽)'
                                }
        else:
            basket['basket'] = {'russian': f'Корзина 🛒({int(amount)} шт. на {self.format_price(float(sum_basket))})',
                                'armenian': f'Զամբյուղ 🛒({int(amount)} հատ {self.format_price(float(sum_basket))})',
                                'azerbaijani': f'Səbət 🛒({int(amount)} ədəd {self.format_price(float(sum_basket))})',
                                'english': f'Basket 🛒({int(amount)} pieces per {self.format_price(float(sum_basket))})',
                                'georgian': f'კალათა 🛒({int(amount)} ცალი {self.format_price(float(sum_basket))})',
                                'kazakh': f'Себет 🛒({int(amount)} дана {self.format_price(float(sum_basket))})',
                                'kyrgyz': f'Себет 🛒({int(amount)} даана {self.format_price(float(sum_basket))})',
                                'mongolian': f'Сагс 🛒({int(amount)} ширхэг тутамд '
                                             f'{self.format_price(float(sum_basket))})',
                                'tajik': f'Сабад 🛒({int(amount)} дона ба {self.format_price(float(sum_basket))})',
                                'uzbek': f'Savat 🛒({int(amount)} dona {self.format_price(float(sum_basket))})',
                                }
        return basket

    @staticmethod
    def format_price(item: float):
        return '{0:,} ₽'.format(item).replace(',', ' ')

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"
