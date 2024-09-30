import os
from dotenv import load_dotenv
from dispatcher import BotTelegram

if __name__ == '__main__':
    load_dotenv()
    bot = BotTelegram(os.environ["BOT_TOKEN"])
    bot.run()
