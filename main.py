import os
from dotenv import load_dotenv
from classes import BotTelegram

if __name__ == '__main__':
    load_dotenv(dotenv_path=os.path.join(os.path.split(os.path.dirname(__file__))[0], 'data/.env'))
    bot = BotTelegram(os.getenv('BOT_TOKEN'))
    bot.run()
