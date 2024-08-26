import os
import logging
import detectlanguage
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

logging.basicConfig(level=logging.INFO)
load_dotenv()


class Language:
    def __init__(self):
        self.source_language = 'russian'
        self.detect_key = os.environ["DETECT_LANGUAGE_API"]

    async def translated_from_russian(self, language_translate: str, text_to_translate: str):
        if language_translate == 'russian':
            translations = text_to_translate
        else:
            translator = GoogleTranslator(source=self.source_language, target=language_translate)
            translations = translator.translate(text=text_to_translate)
        return translations

    async def translated_by_search(self, language_translate: str, text_to_translate: str):
        if language_translate == 'russian':
            translations = text_to_translate
        else:
            detectlanguage.configuration.api_key = self.detect_key
            target_language = detectlanguage.simple_detect(text_to_translate)
            print(target_language)
            translator = GoogleTranslator(source=target_language, target='russian')
            translations = translator.translate(text=text_to_translate)
        return translations


# translator_to_bot = Language()
# start = time.time()
# total = translator_to_bot.translated_by_search('mongolian', 'R10')
# print(total)
# finish = time.time()
#
# # вычитаем время старта из времени окончания и получаем результат в миллисекундах
# res = finish - start
# res_msec = res * 1000
# print('Время работы в миллисекундах: ', res_msec)
