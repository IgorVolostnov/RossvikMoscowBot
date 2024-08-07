import os
from dotenv import load_dotenv
from classes import BotTelegram

if __name__ == '__main__':
    load_dotenv()
    bot = BotTelegram(os.environ["BOT_TOKEN"])
    bot.run()
