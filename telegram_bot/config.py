import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота (получите у @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', '8572835537:AAHXnSkQ_ElpO0t3_p99ugg13gszEgrm7o8')

# Путь к базе данных
DATABASE_PATH = 'it_jobs.db'

# Настройки бота
BOT_SETTINGS = {
    'parse_mode': 'HTML',
    'disable_web_page_preview': True
}