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
        text_news = await self.get_news
        text_order = await self.get_order(id_user)
        text_basket = await self.get_basket(id_user)
        text_catalog = await self.get_catalog
        text_update = await self.get_update
        text_add_status = await self.get_add_status
        if status_user == 'creator':
            text_first_keyboard = {'https://t.me/rossvik_moscow': text_news[user_language],
                                   'orders': text_order[user_language],
                                   'basket': text_basket[user_language],
                                   'catalog': text_catalog[user_language],
                                   'update': text_update[user_language],
                                   'add_status': text_add_status[user_language]}
        elif status_user == 'admin':
            text_first_keyboard = {'https://t.me/rossvik_moscow': text_news[user_language],
                                   'orders': text_order[user_language],
                                   'basket': text_basket[user_language],
                                   'catalog': text_catalog[user_language],
                                   'add_status': text_add_status[user_language]}
        else:
            text_first_keyboard = {'https://t.me/rossvik_moscow': text_news[user_language],
                                   'orders': text_order[user_language],
                                   'basket': text_basket[user_language],
                                   'catalog': text_catalog[user_language]}
        return text_first_keyboard

    @property
    async def get_news(self) -> dict:
        news = {'russian': 'Новости 📣🌐💬',
                'armenian': 'Նորություններ 📣🌐💬',
                'azerbaijani': 'Xəbərlər 📣🌐💬',
                'english': 'News 📣🌐💬',
                'georgian': 'ახალი ამბები 📣🌐💬',
                'kazakh': 'Жаңалықтар 📣🌐💬',
                'kyrgyz': 'Жаңылыктар 📣🌐💬',
                'mongolian': 'Мэдээ 📣🌐💬',
                'tajik': 'Ахбор 📣🌐💬',
                'uzbek': 'Янгиликлар 📣🌐💬'
                }
        return news

    async def get_order(self, id_user: int) -> dict:
        amount = await self.execute.get_amount_order(id_user)
        if amount is None:
            order = {'russian': 'Мои Заказы 🗃️',
                     'armenian': 'Իմ Պատվերները 🗃️',
                     'azerbaijani': 'Sifarişlərim 🗃️',
                     'english': 'My Orders 🗃️',
                     'georgian': 'ჩემი ბრძანებები 🗃️',
                     'kazakh': 'Менің Тапсырыстарым 🗃️',
                     'kyrgyz': 'Менин Буйруктарым 🗃️',
                     'mongolian': 'Миний Захиалга 🗃️',
                     'tajik': 'Фармоишҳои Ман 🗃️',
                     'uzbek': 'Менинг Буюртмаларим 🗃️'
                     }
        else:
            order = {'russian': f'Мои Заказы 🗃️ (Новых заказов: {str(amount)})',
                     'armenian': f'Իմ Պատվերները 🗃️ (Նոր պատվերներ: {str(amount)})',
                     'azerbaijani': f'Sifarişlərim 🗃️ (Yeni sifarişlər: {str(amount)})',
                     'english': f'My Orders 🗃️ (New orders: {str(amount)})',
                     'georgian': f'ჩემი ბრძანებები 🗃️ (ახალი ბრძანებები: {str(amount)})',
                     'kazakh': f'Менің Тапсырыстарым 🗃️ (Жаңа тапсырыстар: {str(amount)})',
                     'kyrgyz': f'Менин Буйруктарым 🗃️ (Жаңы буйруктар: {str(amount)})',
                     'mongolian': f'Миний Захиалга 🗃️ (Шинэ захиалга: {str(amount)})',
                     'tajik': f'Фармоишҳои Ман 🗃️ (Фармоишҳои нав: {str(amount)})',
                     'uzbek': f'Менинг Буюртмаларим 🗃 (Янги буюртмалар: {str(amount)})',
                     }
        return order

    async def get_basket(self, id_user: int) -> dict:
        amount = await self.execute.current_amount_basket(id_user)
        if amount is None:
            basket = {'russian': 'Корзина 🛒(0 шт. на 0 ₽)',
                      'armenian': 'Զամբյուղ 🛒(0 հատ 0 ₽)',
                      'azerbaijani': 'Səbət 🛒(0 ədəd 0 ₽)',
                      'english': 'Basket 🛒(0 pieces per 0 ₽)',
                      'georgian': 'კალათა 🛒(0 ცალი 0 ₽)',
                      'kazakh': 'Себет 🛒(0 дана 0 ₽)',
                      'kyrgyz': 'Себет 🛒(0 даана 0 ₽)',
                      'mongolian': 'Сагс 🛒(0 ширхэг тутамд 0 ₽)',
                      'tajik': 'Сабад 🛒(0 дона ба 0 ₽)',
                      'uzbek': 'Сават 🛒(0 бошига дона 0 ₽)'
                      }
        else:
            sum_basket = await self.execute.current_sum_basket(id_user)
            basket = {'russian': f'Корзина 🛒({int(amount)} шт. на {self.format_price(float(sum_basket))})',
                      'armenian': f'Զամբյուղ 🛒({int(amount)} հատ {self.format_price(float(sum_basket))})',
                      'azerbaijani': f'Səbət 🛒({int(amount)} ədəd {self.format_price(float(sum_basket))})',
                      'english': f'Basket 🛒({int(amount)} pieces per {self.format_price(float(sum_basket))})',
                      'georgian': f'კალათა 🛒({int(amount)} ცალი {self.format_price(float(sum_basket))})',
                      'kazakh': f'Себет 🛒({int(amount)} дана {self.format_price(float(sum_basket))})',
                      'kyrgyz': f'Себет 🛒({int(amount)} даана {self.format_price(float(sum_basket))})',
                      'mongolian': f'Сагс 🛒({int(amount)} ширхэг тутамд {self.format_price(float(sum_basket))})',
                      'tajik': f'Сабад 🛒({int(amount)} дона ба {self.format_price(float(sum_basket))})',
                      'uzbek': f'Сават 🛒({int(amount)} бошига дона {self.format_price(float(sum_basket))})',
                      }
        return basket

    @property
    async def get_catalog(self) -> dict:
        catalog = {'russian': 'Каталог 🧾👀',
                   'armenian': 'Կատալոգ 🧾👀',
                   'azerbaijani': 'Kataloq 🧾👀',
                   'english': 'Catalog 🧾👀',
                   'georgian': 'კატალოგი 🧾👀',
                   'kazakh': 'Каталог 🧾👀',
                   'kyrgyz': 'Каталог 🧾👀',
                   'mongolian': 'Каталог 🧾👀',
                   'tajik': 'Каталоги 🧾👀',
                   'uzbek': 'Каталог 🧾👀'
                   }
        return catalog

    @property
    async def get_update(self) -> dict:
        update = {'russian': 'Обновить сообщения 💬',
                  'armenian': 'Թարմացնել հաղորդագրությունները 💬',
                  'azerbaijani': 'Mesajları yeniləyin 💬',
                  'english': 'Update messages 💬',
                  'georgian': 'შეტყობინებების განახლება 💬',
                  'kazakh': 'Хабарламаларды жаңарту 💬',
                  'kyrgyz': 'Билдирүүлөрдү жаңыртуу 💬',
                  'mongolian': 'Билдирүүлөрдү жаңыртуу 💬',
                  'tajik': 'Паемҳоро навсозӣ кунед 💬',
                  'uzbek': 'Хабарларни янгиланг 💬'
                  }
        return update

    @property
    async def get_add_status(self) -> dict:
        add_status = {'russian': 'Присвоить статус 😎',
                      'armenian': 'Կարգավիճակ շնորհել 😎',
                      'azerbaijani': 'Status verin 😎',
                      'english': 'Assign a status 😎',
                      'georgian': 'სტატუსის მინიჭება 😎',
                      'kazakh': 'Мәртебе беру 😎',
                      'kyrgyz': 'Статус берүү 😎',
                      'mongolian': 'Байдал даалгах 😎',
                      'tajik': 'Додани мақом 😎',
                      'uzbek': 'Мақомни тайинлаш 😎'
                      }
        return add_status

    @property
    async def get_start_message(self) -> dict:
        start_message = {'russian': 'Выберите, что Вас интересует ⤵ ⤵ ⤵',
                         'armenian': 'Ընտրեք, թե ինչն է ձեզ հետաքրքրում ⤵ ⤵ ⤵',
                         'azerbaijani': 'Sizi maraqlandıran şeyləri seçin ⤵ ⤵ ⤵',
                         'english': 'Choose what interests you ⤵ ⤵ ⤵',
                         'georgian': 'აირჩიეთ ის, რაც გაინტერესებთ ⤵ ⤵ ⤵',
                         'kazakh': 'Сізді не қызықтыратынын таңдаңыз ⤵ ⤵ ⤵',
                         'kyrgyz': 'Сизди эмне кызыктырарын тандаңыз ⤵ ⤵ ⤵',
                         'mongolian': 'Та юу сонирхож байгаагаа сонгоно уу ⤵ ⤵ ⤵',
                         'tajik': 'Чизеро, ки Ба шумо маъқул аст, интихоб кунед ⤵ ⤵ ⤵',
                         'uzbek': 'Сизни қизиқтирган нарсани танланг ⤵ ⤵ ⤵'
                         }
        return start_message

    async def get_info_help(self, user_language: str) -> str:
        text_first_string = await self.get_first_string
        text_main_menu = await self.get_main_menu
        text_catalog = await self.get_catalog
        text_news = await self.get_news
        text_basket_help = await self.get_basket_help
        text_order_help = await self.get_order_help
        text_search_help = await self.get_search_help
        text_second_string = await self.get_second_string
        text_privacy_notice = await self.get_privacy_notice
        text_third_string = await self.get_third_string
        text_help = f'{text_first_string[user_language]}\n' \
                    f'/start - <b>{text_main_menu[user_language]}</b>\n' \
                    f'/catalog - <b>{text_catalog[user_language]}</b>\n' \
                    f'/news - <b>{text_news[user_language]}</b>\n' \
                    f'/basket - <b>{text_basket_help[user_language]}</b>\n' \
                    f'/order - <b>{text_order_help[user_language]}</b>\n' \
                    f'<b>{text_search_help[user_language]}</b>\n' \
                    f'{text_second_string[user_language]}\n' \
                    f'<code>пласт вст</code>\n' \
                    f'<b>{text_privacy_notice[user_language]}</b>\n' \
                    f'{text_third_string[user_language]}'
        return text_help

    @property
    async def get_first_string(self) -> dict:
        first_string = {'russian': 'Вы можете воспользоваться быстрой навигацией, отправляя следующие команды:',
                        'armenian': 'Կարող եք օգտվել արագ նավարկությունից ՝ ուղարկելով հետևյալ հրամանները:',
                        'azerbaijani': 'Aşağıdakı əmrləri göndərərək sürətli naviqasiyadan faydalana bilərsiniz:',
                        'english': 'You can take advantage of quick navigation by sending the following commands:',
                        'georgian': 'თქვენ შეგიძლიათ ისარგებლოთ სწრაფი ნავიგაციით შემდეგი ბრძანებების გაგზავნით:',
                        'kazakh': 'Келесі пәрмендерді жіберу арқылы жылдам навигацияны пайдалануға болады:',
                        'kyrgyz': 'Төмөнкү буйруктарды жөнөтүп, тез навигациянын пайдасын көрө аласыз:',
                        'mongolian': 'Та дараах тушаалуудыг илгээж хурдан навигацийн давуу талыг ашиглах боломжтой:',
                        'tajik': 'Шумо метавонед бо фиристодани фармонҳои зерин аз новбари зуд истифода баред:',
                        'uzbek': 'Қуйидаги буйруқларни юбориш орқали тезкор навигациядан фойдаланишингиз мумкин:'
                        }
        return first_string

    @property
    async def get_main_menu(self) -> dict:
        main_menu = {'russian': 'Главное меню 📋📱',
                     'armenian': 'Գլխավոր Մենյու 📋📱',
                     'azerbaijani': 'Əsas menyu 📋📱',
                     'english': 'Əsas menyu 📋📱',
                     'georgian': 'Əsas menyu 📋📱',
                     'kazakh': 'Əsas menyu 📋📱',
                     'kyrgyz': 'Башкы меню 📋📱',
                     'mongolian': 'Башкы меню 📋📱',
                     'tajik': 'Менюи асосӣ 📋📱',
                     'uzbek': 'Асосий Меню 📋📱'
                     }
        return main_menu

    @property
    async def get_basket_help(self) -> dict:
        basket_help = {'russian': 'Корзина 🛒',
                       'armenian': 'Զամբյուղ 🛒',
                       'azerbaijani': 'Səbət 🛒',
                       'english': 'Basket 🛒',
                       'georgian': 'კალათა 🛒',
                       'kazakh': 'Себет 🛒',
                       'kyrgyz': 'Себет 🛒',
                       'mongolian': 'Сагс 🛒',
                       'tajik': 'Сабад 🛒',
                       'uzbek': 'Сават 🛒'
                       }
        return basket_help

    @property
    async def get_order_help(self) -> dict:
        order_help = {'russian': 'Мои Заказы 🗃️',
                      'armenian': 'Իմ Պատվերները 🗃️',
                      'azerbaijani': 'Sifarişlərim 🗃️',
                      'english': 'My Orders 🗃️',
                      'georgian': 'ჩემი ბრძანებები 🗃️',
                      'kazakh': 'Менің Тапсырыстарым 🗃️',
                      'kyrgyz': 'Менин Буйруктарым 🗃️',
                      'mongolian': 'Миний Захиалга 🗃️',
                      'tajik': 'Фармоишҳои Ман 🗃️',
                      'uzbek': 'Менинг Буюртмаларим 🗃️'
                      }
        return order_help

    @property
    async def get_search_help(self) -> dict:
        search_help = {'russian': 'Поиск товара 🔎:',
                       'armenian': 'Ապրանքի որոնում 🔎:',
                       'azerbaijani': 'Məhsul axtarışı 🔎:',
                       'english': 'Product Search 🔎:',
                       'georgian': 'პროდუქტის ძებნა 🔎:',
                       'kazakh': 'Өнімді іздеу 🔎:',
                       'kyrgyz': 'Продукт издөө 🔎:',
                       'mongolian': 'Бүтээгдэхүүний Хайлт 🔎:',
                       'tajik': 'Ҷустуҷӯи мол 🔎:',
                       'uzbek': 'Маҳсулот Қидириш 🔎:'
                       }
        return search_help

    @property
    async def get_second_string(self) -> dict:
        second_string = {'russian': 'При отправке боту сообщения происходит поиск товара в каталоге по содержимому '
                                    'сообщения, разделенному пробелами. Можно указывать не только слова, но и символы, '
                                    'которые содержатся в наименовании товара. Чтобы понять, как это работает, '
                                    'попробуйте отправить боту сообщение:',
                         'armenian': 'Հաղորդագրության բոտը ուղարկելիս կատալոգում ապրանքը որոնվում է Ըստ '
                                     'հաղորդագրության բովանդակության, որը բաժանված է բացատներով: Կարող եք նշել ոչ '
                                     'միայն բառերը, այլև խորհրդանիշները, որոնք պարունակվում են ապրանքի անվանման մեջ: '
                                     'Հասկանալու համար, թե ինչպես է այն աշխատում, փորձեք հաղորդագրություն ուղարկել '
                                     'բոտին:',
                         'azerbaijani': 'Mesaj botuna göndərildikdə, məhsul Kataloqda boşluqlarla ayrılmış mesajın '
                                        'məzmununa görə axtarılır. Yalnız sözləri deyil, Məhsulun adında olan '
                                        'simvolları da göstərə bilərsiniz. Bunun necə işlədiyini anlamaq üçün '
                                        'botunuza bir mesaj göndərməyə çalışın:',
                         'english': 'When sending a message to the bot, the product is searched in the catalog by '
                                    'the contents of the message, separated by spaces. You can specify not only the '
                                    'words, but also the symbols that are contained in the product name. To '
                                    'understand how it works, try sending a message to the bot:',
                         'georgian': 'ბოტისთვის შეტყობინების გაგზავნისას, პროდუქტი კატალოგში იძებნება შეტყობინების '
                                     'შინაარსით, გამოყოფილი სივრცეებით. თქვენ შეგიძლიათ მიუთითოთ არა მხოლოდ სიტყვები, '
                                     'არამედ სიმბოლოები, რომლებიც შეიცავს პროდუქტის სახელს. იმის გასაგებად, თუ როგორ '
                                     'მუშაობს, შეეცადეთ გაუგზავნოთ შეტყობინება ბოტს:',
                         'kazakh': 'Хабарламаны ботқа жіберген кезде, ол бос орындармен бөлінген хабарламаның мазмұны '
                                   'бойынша каталогтан тауарды іздейді. Сіз тек сөздерді ғана емес, сонымен қатар '
                                   'тауардың атауында кездесетін белгілерді де көрсете аласыз. Оның қалай жұмыс '
                                   'істейтінін түсіну үшін ботқа хабарлама жіберіп көріңіз:',
                         'kyrgyz': 'Ботко билдирүү жөнөтүүдө, каталогдо боштук менен бөлүнгөн Билдирүүнүн мазмуну '
                                   'боюнча издөө жүргүзүлөт. Сиз сөздөрдү гана эмес, товардын аталышында камтылган '
                                   'символдорду да көрсөтө аласыз. Бул кантип иштээрин түшүнүү үчүн, ботко билдирүү '
                                   'жөнөтүп көрүңүз:',
                         'mongolian': 'Бот руу мессеж илгээхдээ бүтээгдэхүүнийг орон зайгаар тусгаарласан мессежийн '
                                      'агуулгаар каталогт хайна. Та зөвхөн үгсийг төдийгүй бүтээгдэхүүний нэрэнд '
                                      'агуулагдах тэмдэглэгээг зааж өгч болно. Энэ нь хэрхэн ажилладагийг ойлгохын '
                                      'тулд bot руу мессеж илгээж үзээрэй:',
                         'tajik': 'Ҳангоми фиристодани боти паем, ҷустуҷӯи мол дар каталог аз рӯи мундариҷаи паем, '
                                  'ки бо фосилаҳо ҷудо карда шудааст, сурат мегирад. На танҳо калимаҳо, балки рамзҳое, '
                                  'ки дар номи мол мавҷуданд, нишон дода мешаванд. Барои фаҳмидани он, ки ин чӣ гуна '
                                  'кор мекунад, кӯшиш кунед, ки ба бот паем фиристед:',
                         'uzbek': 'Ботга хабар юборишда маҳсулот каталогда бўш жойлар билан ажратилган хабар мазмуни '
                                  'бўйича қидирилади. Сиз нафақат сўзларни, балки маҳсулот номидаги белгиларни ҳам '
                                  'белгилашингиз мумкин. Унинг қандай ишлашини тушуниш учун ботга хабар юборишга '
                                  'ҳаракат қилинг:'
                         }
        return second_string

    @property
    async def get_privacy_notice(self) -> dict:
        privacy_notice = {'russian': 'УВЕДОМЛЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ:',
                          'armenian': 'ԳԱՂՏՆԻՈՒԹՅԱՆ ՄԱՍԻՆ ԾԱՆՈՒՑՈՒՄ:',
                          'azerbaijani': 'MƏXFİLİK BİLDİRİŞİ:',
                          'english': 'PRIVACY NOTICE:',
                          'georgian': 'კონფიდენციალურობის შეტყობინება:',
                          'kazakh': 'ҚҰПИЯЛЫЛЫҚ ТУРАЛЫ ХАБАРЛАМА:',
                          'kyrgyz': 'КУПУЯЛЫК ЭСКЕРТҮҮСҮ:',
                          'mongolian': 'НУУЦЛАЛЫН МЭДЭГДЭЛ:',
                          'tajik': 'ОГОҲИНОМА ДАР БОРАИ МАХФИЯТ:',
                          'uzbek': 'МАХФИЙЛИК ХАБАРНОМАСИ:'
                          }
        return privacy_notice

    @property
    async def get_third_string(self) -> dict:
        third_string = {'russian': 'Все данные, полученные в процессе взаимодействия между Ботом и Пользователем: '
                                   'фото, видео, текстовая информация, а также любые отправленные документы, которые '
                                   'содержат конфиденциальную информацию не подлежат использованию, копированию, '
                                   'распространению, а также осуществлению любых других действий на их основе.',
                        'armenian': 'Բոտի և օգտագործողի միջև փոխգործակցության ընթացքում ձեռք բերված բոլոր տվյալները ՝ '
                                    'լուսանկարներ, տեսանյութեր, տեքստային տեղեկություններ, ինչպես նաև ցանկացած '
                                    'ուղարկված փաստաթղթեր, որոնք պարունակում են գաղտնի տեղեկատվություն, ենթակա չեն '
                                    'օգտագործման, պատճենահանման, տարածման, ինչպես նաև դրանց հիման վրա ցանկացած այլ '
                                    'գործողությունների իրականացման:',
                        'azerbaijani': 'Bot və istifadəçi arasında qarşılıqlı əlaqə prosesində əldə edilən bütün '
                                       'məlumatlar: fotoşəkillər, videolar, mətn məlumatları, habelə məxfi '
                                       'məlumatları ehtiva edən hər hansı bir sənəd istifadə edilə bilməz, kopyalana '
                                       'bilməz, paylaşıla bilməz, habelə onlara əsaslanan hər hansı digər '
                                       'hərəkətlərin həyata keçirilməsi.',
                        'english': 'All data obtained during the interaction between the Bot and the User: photos, '
                                   'videos, text information, as well as any sent documents that contain confidential '
                                   'information are not subject to use, copying, distribution, as well as any other '
                                   'actions based on them.',
                        'georgian': 'ბოტსა და მომხმარებელს შორის ურთიერთქმედების დროს მიღებული ყველა მონაცემი: '
                                    'ფოტოები, ვიდეოები, ტექსტური ინფორმაცია, ასევე ნებისმიერი გაგზავნილი დოკუმენტი, '
                                    'რომელიც შეიცავს კონფიდენციალურ ინფორმაციას, არ ექვემდებარება გამოყენებას, '
                                    'კოპირებას, განაწილებას, ისევე როგორც მათზე დაფუძნებულ სხვა ქმედებებს.',
                        'kazakh': 'Бот пен пайдаланушы арасындағы өзара іс-қимыл процесінде алынған барлық деректер: '
                                  'фотосуреттер, бейнелер, мәтіндік ақпарат, сондай-ақ құпия ақпаратты қамтитын кез '
                                  'келген жіберілген құжаттар пайдалануға, көшіруге, таратуға, сондай-ақ олардың '
                                  'негізінде кез келген басқа әрекеттерді жүзеге асыруға жатпайды.',
                        'kyrgyz': 'Бот менен пайдалануучунун ортосундагы өз ара аракеттенүү процессинде алынган '
                                  'бардык маалыматтар: фото, видео, тексттик маалымат, ошондой эле купуя маалыматты '
                                  'камтыган бардык жөнөтүлгөн документтер пайдаланууга, көчүрүүгө, жайылтууга, ошондой '
                                  'эле алардын негизинде кайсы болбосун башка аракеттерди жүзөгө ашырууга жатпайт.',
                        'mongolian': 'Bot болон хэрэглэгчийн хоорондын харилцан үйлчлэлийн явцад олж авсан бүх '
                                     'өгөгдөл: зураг, видео, текстийн мэдээлэл, түүнчлэн нууц мэдээллийг агуулсан '
                                     'илгээсэн баримт бичгийг ашиглах, хуулбарлах, түгээх, түүнчлэн тэдгээрт '
                                     'үндэслэсэн бусад үйлдэлд хамаарахгүй.',
                        'tajik': 'Ҳамаи маълумотҳое, ки дар ҷараени ҳамкории Байни Бот ва Корбар ба даст оварда '
                                 'шудаанд: аксҳо, видеоҳо, маълумоти матнӣ, инчунин ҳама гуна ҳуҷҷатҳои фиристодашуда, '
                                 'ки дорои маълумоти махфӣ мебошанд, набояд истифода шаванд, нусхабардорӣ карда '
                                 'шаванд, паҳн карда шаванд ва инчунин ҳама гуна амалҳои дигар дар асоси онҳо '
                                 'амалӣ карда шаванд.',
                        'uzbek': 'Бот ва фойдаланувчи ўртасидаги ўзаро таъсир пайтида олинган барча маълумотлар: '
                                 'фотосуратлар, видеолар, матнли маълумотлар, шунингдек махфий маълумотларни ўз ичига '
                                 'олган ҳар қандай юборилган ҳужжатлар фойдаланиш, нусхалаш, тарқатиш, шунингдек '
                                 'уларга асосланган бошқа ҳаракатлар.'
                        }
        return third_string

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
        for item in range(4000, 40000):
            dict_nomenclature[str(item)] = str(item)
        return dict_nomenclature

    @property
    def get_dealer_price_remove(self):
        dict_dealer_price_remove = {}
        for item in range(4000, 40000):
            dict_dealer_price_remove[f'{str(item)}remove_dealer_price'] = str(item)
        return dict_dealer_price_remove

    @property
    def get_dealer_price_show(self):
        dict_dealer_price_show = {}
        for item in range(4000, 40000):
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
            for id_nomenclature in range(4000, 40000):
                dict_button_calculater[f'{str(id_nomenclature)}///{str(item)}'] = str(item)
        return dict_button_calculater

    @staticmethod
    def get_dict_value(value: str, start: int, finish: int):
        dict_value = {}
        for item in range(start, finish):
            dict_value[f'{str(item)}{value}'] = str(item)
        return dict_value

    @staticmethod
    def format_price(item: float):
        return '{0:,} ₽'.format(item).replace(',', ' ')

    @staticmethod
    def quote(request):
        return f"'{str(request)}'"
