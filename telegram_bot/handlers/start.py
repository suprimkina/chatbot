from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import CallbackContext
from telegram_bot.database import db_manager


async def start_command(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user

    # Создаем клавиатуру главного меню
    keyboard = [
        [KeyboardButton("🎯 Выбрать направление")],
        [KeyboardButton("📊 Получить задачу"), KeyboardButton("🛠️ Топ навыки")],
        [KeyboardButton("📈 Статистика"), KeyboardButton("ℹ️ О боте")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = f"""
👋 Привет, {user.first_name}!

Я - бот для подготовки к IT-собеседованиям. 

Я помогу тебе:
• 🎯 Выбрать направление подготовки
• 📊 Получать задачи разной сложности
• 🛠️ Узнать востребованные навыки
• 📈 Изучить статистику рынка труда

Выбери действие в меню ниже👇
    """

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def about_command(update: Update, context: CallbackContext):
    """Обработчик команды 'О боте'"""
    about_text = """
🤖 <b>IT Career Helper Bot</b>

Этот бот создан для помощи в подготовке к IT-собеседованиям на основе анализа реальных данных с HH.ru.

<b>Возможности:</b>
• Подбор задач по направлениям
• Статистика востребованных навыков
• Анализ рынка труда
• Подготовка к реальным собеседованиям

База данных обновляется регулярно на основе актуальных вакансий.

📊 <b>Статистика базы данных:</b>
• 1000+ вакансий
• 50+ направлений разработки
• 200+ навыков и технологий

Удачи в подготовке! 🚀
    """
    await update.message.reply_text(about_text, parse_mode='HTML')