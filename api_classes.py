import requests
import json
import re
from stdnum.exceptions import *
from stdnum.util import clean, isdigits


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


def compact(number):
    """Convert the number to the minimal representation. This strips the
    number of any valid separators and removes surrounding whitespace."""
    return clean(number, ' ').strip()


def calc_company_check_digit(number):
    """Calculate the check digit for the 10-digit ИНН for organisations."""
    weights = (2, 4, 10, 3, 5, 9, 4, 6, 8)
    return str(sum(w * int(n) for w, n in zip(weights, number)) % 11 % 10)


def calc_personal_check_digits(number):
    """Calculate the check digits for the 12-digit personal ИНН."""
    weights = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
    d1 = str(sum(w * int(n) for w, n in zip(weights, number)) % 11 % 10)
    weights = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
    d2 = str(sum(w * int(n) for w, n in zip(weights, number[:10] + d1)) % 11 % 10)
    return d1 + d2


def validate(number):
    """Check if the number is a valid ИНН. This checks the length, formatting
    and check digit."""
    number = compact(number)
    if not isdigits(number):
        raise InvalidFormat()
    if len(number) == 10:
        if calc_company_check_digit(number) != number[-1]:
            raise InvalidChecksum()
    elif len(number) == 12:
        # persons
        if calc_personal_check_digits(number) != number[-2:]:
            raise InvalidChecksum()
    else:
        raise InvalidLength()
    return number


def is_valid(number):
    """Check if the number is a valid ИНН."""
    try:
        return bool(validate(number))
    except ValidationError:
        return False


check = is_valid('463001656103')
print(check)
