import os
import logging
import detectlanguage
from deep_translator import GoogleTranslator

logging.basicConfig(level=logging.INFO)


class Language:
    def __init__(self):
        self.source_language = 'russian'
        self.detect_key = os.environ["DETECT_LANGUAGE_API"]

    async def translated_from_russian(self, language_translate: str, text_to_translate: list) -> list:
        if language_translate == 'russian':
            translations = text_to_translate
        else:
            translator = GoogleTranslator(source=self.source_language, target=language_translate)
            if len(text_to_translate) == 1:
                translations = [translator.translate(text=text_to_translate[0])]
            else:
                translations = translator.translate_batch(batch=text_to_translate)
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
# total = asyncio.run(translator_to_bot.translated_from_russian('mongolian', ['Двухслойные латки Rossvik.']))
# print(total)
# finish = time.time()
# # вычитаем время старта из времени окончания и получаем результат в миллисекундах
# res = finish - start
# res_msec = res * 1000
# print('Время работы в миллисекундах: ', res_msec)
