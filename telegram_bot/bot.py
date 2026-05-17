import os
import logging
import random
import asyncio
import signal
import sys
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from dotenv import load_dotenv
from error_analyzer import ErrorAnalyzer

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# NEW: инициализация анализатора (модель должна быть в той же папке)
try:
    error_analyzer = ErrorAnalyzer()
    logger.info("ErrorAnalyzer успешно загружен")
except Exception as e:
    logger.error(f"Не удалось загрузить модель анализатора: {e}")
    error_analyzer = None


class BotMenus:
    @staticmethod
    def main_menu():
        keyboard = [
            [KeyboardButton("🎯 Выбрать направление")],
            [KeyboardButton("📊 Получить задачу")],
            [KeyboardButton("🛠️ Топ навыки")],
            [KeyboardButton("📈 Статистика")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def tasks_menu():
        keyboard = [
            [KeyboardButton("🐍 Python задачи")],
            [KeyboardButton("🌐 Frontend задачи")],
            [KeyboardButton("📊 Data Science задачи")],
            [KeyboardButton("☕ Java задачи"), KeyboardButton("🔧 DevOps задачи")],
            [KeyboardButton("🎲 Случайная задача"), KeyboardButton("🔙 Главное меню")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def difficulty_menu():
        keyboard = [
            [KeyboardButton("🟢 Легкие задачи")],
            [KeyboardButton("🟡 Средние задачи")],
            [KeyboardButton("🔴 Сложные задачи")],
            [KeyboardButton("🎲 Любая сложность"), KeyboardButton("🔙 Назад к задачам")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def task_actions_menu():
        keyboard = [
            [KeyboardButton("👀 Показать решение"), KeyboardButton("✏️ Отправить решение")],  # NEW кнопка
            [KeyboardButton("🔄 Новая задача")],
            [KeyboardButton("📊 Выбрать категорию"), KeyboardButton("🔙 Главное меню")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    @staticmethod
    def remove_menu():
        return ReplyKeyboardRemove()


class TaskManager:
    @staticmethod
    def get_tasks():
        return {
            "python": [
                {
                    "title": "FizzBuzz",
                    "description": "Напишите программу, которая выводит числа от 1 до 100. Но для кратных трём выводите 'Fizz', для кратных пяти - 'Buzz', а для кратных и трём, и пяти - 'FizzBuzz'.",
                    "difficulty": "🟢 Легкая",
                    "solution": "for i in range(1, 101):\n    if i % 15 == 0:\n        print('FizzBuzz')\n    elif i % 3 == 0:\n        print('Fizz')\n    elif i % 5 == 0:\n        print('Buzz')\n    else:\n        print(i)",
                    "type": "algorithm"
                },
                {
                    "title": "Two Sum",
                    "description": "Дан массив целых чисел и целевое число. Найдите индексы двух чисел, которые в сумме дают целевое число.",
                    "difficulty": "🟢 Легкая",
                    "solution": "def two_sum(nums, target):\n    num_map = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in num_map:\n            return [num_map[complement], i]\n        num_map[num] = i\n    return []",
                    "type": "algorithm"
                }
            ],
            "frontend": [
                {
                    "title": "Debounce Function",
                    "description": "Реализуйте функцию debounce, которая откладывает вызов функции до истечения задержки после последнего вызова.",
                    "difficulty": "🟡 Средняя",
                    "solution": "function debounce(func, delay) {\n    let timeoutId;\n    return function(...args) {\n        clearTimeout(timeoutId);\n        timeoutId = setTimeout(() => func.apply(this, args), delay);\n    };\n}",
                    "type": "algorithm"
                }
            ],
            "data_science": [
                {
                    "title": "SQL Second Highest Salary",
                    "description": "Напишите SQL запрос для нахождения второй по величине зарплаты из таблицы employees.",
                    "difficulty": "🟡 Средняя",
                    "solution": "SELECT MAX(salary) as SecondHighestSalary\nFROM employees\nWHERE salary < (SELECT MAX(salary) FROM employees)",
                    "type": "sql"
                }
            ],
            "java": [
                {
                    "title": "Singleton Pattern",
                    "description": "Реализуйте потокобезопасный Singleton pattern в Java.",
                    "difficulty": "🟡 Средняя",
                    "solution": "public class Singleton {\n    private static volatile Singleton instance;\n    \n    private Singleton() {}\n    \n    public static Singleton getInstance() {\n        if (instance == null) {\n            synchronized (Singleton.class) {\n                if (instance == null) {\n                    instance = new Singleton();\n                }\n            }\n        }\n        return instance;\n    }\n}",
                    "type": "design_pattern"
                }
            ],
            "devops": [
                {
                    "title": "Dockerfile Optimization",
                    "description": "Напишите оптимизированный Dockerfile для Python приложения.",
                    "difficulty": "🟡 Средняя",
                    "solution": "# Многостадийная сборка\nFROM python:3.9-slim as builder\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --user -r requirements.txt\n\nFROM python:3.9-slim\nWORKDIR /app\nCOPY --from=builder /root/.local /root/.local\nCOPY . .\nENV PATH=/root/.local/bin:$PATH\nCMD ['python', 'app.py']",
                    "type": "devops"
                }
            ]
        }

    @staticmethod
    def get_random_task(category=None, difficulty=None):
        tasks = TaskManager.get_tasks()
        if category and category in tasks:
            pool = tasks[category]
        else:
            pool = [t for cat in tasks.values() for t in cat]

        if difficulty:
            pool = [t for t in pool if t["difficulty"] == difficulty]

        return random.choice(pool) if pool else None

    @staticmethod
    def get_task_by_title(title):
        """NEW: поиск задачи по названию (для получения эталона)"""
        for cat_tasks in TaskManager.get_tasks().values():
            for t in cat_tasks:
                if t["title"] == title:
                    return t
        return None

    @staticmethod
    def format_task(task):
        if not task:
            return "❌ Задачи по выбранным критериям не найдены."
        return (
            f"<b>{task['title']}</b>\n"
            f"📊 <b>Сложность:</b> {task['difficulty']}\n"
            f"🎯 <b>Тип:</b> {task['type']}\n\n"
            f"<u>Задача:</u>\n{task['description']}\n\n"
            f"💡 <i>Пришли своё решение, и я проверю его на ошибки!</i>"
        )

    @staticmethod
    def format_solution(task):
        if not task or not task.get('solution'):
            return "❌ Решение для этой задачи пока не добавлено."
        return f"✅ <b>Решение:</b> {task['title']}\n\n<code>{task['solution']}</code>"


# Глобальные состояния
user_current_tasks = {}
user_waiting_solution = {}  # NEW: флаг, что пользователь хочет отправить решение


async def safe_send_message(update: Update, text: str, reply_markup=None, parse_mode='HTML'):
    try:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")


async def force_new_menu(update, context, message, menu_type="main"):
    try:
        await safe_send_message(update, "🔄 Обновляем меню...", BotMenus.remove_menu())
        await asyncio.sleep(0.5)
        menus = {
            "tasks": BotMenus.tasks_menu(),
            "difficulty": BotMenus.difficulty_menu(),
            "task_actions": BotMenus.task_actions_menu(),
            "main": BotMenus.main_menu()
        }
        await safe_send_message(update, message, menus.get(menu_type, BotMenus.main_menu()))
    except Exception as e:
        logger.error(f"Ошибка force_new_menu: {e}")


# --- Обработчики (start, меню и т.д.) те же, кроме новых ниже ---

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запустил бота")
    await safe_send_message(update, "🔄 Загружаем меню...", BotMenus.remove_menu())
    await asyncio.sleep(0.5)
    await safe_send_message(
        update,
        f"👋 Привет {user.first_name}!\n\nЯ - бот для подготовки к IT-собеседованиям.\n\nВыбери действие в меню ниже:",
        BotMenus.main_menu()
    )


async def handle_choose_direction(update, context):
    directions = [
        "• 🐍 Python-разработчик",
        "• 🌐 Frontend-разработчик",
        "• 📊 Data Science",
        "• ☕ Java-разработчик",
        "• 🔧 DevOps-инженер"
    ]
    await force_new_menu(update, context, "🎯 <b>Доступные направления:</b>\n\n" + "\n".join(directions), "main")


async def handle_get_task(update, context):
    await force_new_menu(update, context, "📊 <b>Выбери категорию задач:</b>", "tasks")


async def handle_task_category(update, context):
    text = update.message.text
    user_id = update.effective_user.id
    category_map = {
        "🐍 Python задачи": "python",
        "🌐 Frontend задачи": "frontend",
        "📊 Data Science задачи": "data_science",
        "☕ Java задачи": "java",
        "🔧 DevOps задачи": "devops",
        "🎲 Случайная задача": "random"
    }
    category = category_map.get(text, "random")
    if user_id not in user_current_tasks:
        user_current_tasks[user_id] = {}
    user_current_tasks[user_id]['category'] = category
    await force_new_menu(update, context, "🎯 <b>Выбери сложность задачи:</b>", "difficulty")


async def handle_difficulty(update, context):
    text = update.message.text
    user_id = update.effective_user.id
    difficulty_map = {
        "🟢 Легкие задачи": "🟢 Легкая",
        "🟡 Средние задачи": "🟡 Средняя",
        "🔴 Сложные задачи": "🔴 Сложная",
        "🎲 Любая сложность": None
    }
    difficulty = difficulty_map.get(text)
    category = user_current_tasks.get(user_id, {}).get('category', 'random')
    task = TaskManager.get_random_task(category, difficulty)
    if task:
        user_current_tasks[user_id]['current_task'] = task
        await safe_send_message(update, TaskManager.format_task(task), BotMenus.task_actions_menu())
    else:
        await safe_send_message(update, "❌ Нет подходящих задач.")


async def handle_show_solution(update, context):
    user_id = update.effective_user.id
    task = user_current_tasks.get(user_id, {}).get('current_task')
    if not task:
        await safe_send_message(update, "❌ Сначала получите задачу!")
        return
    await safe_send_message(update, TaskManager.format_solution(task), BotMenus.task_actions_menu())


async def handle_new_task(update, context):
    user_id = update.effective_user.id
    cat = user_current_tasks.get(user_id, {}).get('category', 'random')
    diff = user_current_tasks.get(user_id, {}).get('current_task', {}).get('difficulty')
    task = TaskManager.get_random_task(cat, diff)
    if task:
        user_current_tasks[user_id]['current_task'] = task
        await safe_send_message(update, TaskManager.format_task(task), BotMenus.task_actions_menu())
    else:
        await safe_send_message(update, "❌ Не удалось подобрать задачу.")


# --- NEW: Обработчики для анализа ошибок ---

async def handle_send_solution(update, context):
    """Кнопка 'Отправить решение' — переводим пользователя в режим ожидания кода"""
    user_id = update.effective_user.id
    task = user_current_tasks.get(user_id, {}).get('current_task')
    if not task:
        await safe_send_message(update, "❌ Сначала получите задачу!")
        return
    user_waiting_solution[user_id] = True
    await safe_send_message(
        update,
        "📥 <b>Отправьте ваше решение одним сообщением (код).</b>\nЯ сравню его с эталоном и укажу на ошибки.",
        BotMenus.remove_menu()
    )


async def handle_user_solution(update, context):
    """Приём кода и анализ, если пользователь находится в режиме ожидания.
       Иначе переадресует в обработчик неизвестных сообщений."""
    user_id = update.effective_user.id
    if not user_waiting_solution.get(user_id):
        # Пользователь не в режиме отправки решения — обрабатываем как неизвестное сообщение
        await handle_unknown_message(update, context)
        return

    # Сбрасываем флаг
    user_waiting_solution[user_id] = False

    task = user_current_tasks.get(user_id, {}).get('current_task')
    if not task or not task.get('solution'):
        await safe_send_message(update, "❌ Нет эталонного решения для сравнения.", BotMenus.task_actions_menu())
        return

    user_code = update.message.text.strip()
    ref_code = task['solution']

    logger.info(f"Анализирую решение пользователя {user_id}...")
    if error_analyzer:
        try:
            result = error_analyzer.analyze(user_code, ref_code)
            response = f"📊 <b>Результат проверки:</b>\n\n{result['explanation']}\n\nТип ошибки: <i>{result['label']}</i>"
        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            response = "❌ Произошла ошибка при анализе кода."
    else:
        response = "❌ Модуль анализа ошибок не загружен."


    await safe_send_message(update, response, BotMenus.task_actions_menu(), parse_mode=None)

async def handle_top_skills(update, context):
    skills = """
🛠️ <b>Топ навыков для junior-разработчиков:</b>
...
"""
    await force_new_menu(update, context, skills, "main")


async def handle_statistics(update, context):
    stats = """
📈 <b>Статистика IT-рынка для juniors:</b>
...
"""
    await force_new_menu(update, context, stats, "main")


async def handle_back_to_main(update, context):
    await force_new_menu(update, context, "Возвращаемся в главное меню:", "main")


async def handle_back_to_tasks(update, context):
    await force_new_menu(update, context, "Выбери категорию задач:", "tasks")


async def handle_unknown_message(update, context):
    await force_new_menu(update, context, "🤔 Используйте кнопки меню.", "main")


async def error_handler(update, context):
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await safe_send_message(update, "❌ Произошла ошибка. Попробуйте ещё раз.", BotMenus.main_menu())


def signal_handler(signum, frame):
    logger.info(f"Сигнал {signum}. Завершение...")
    sys.exit(0)


def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден")
        return

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_error_handler(error_handler)

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("🎯 Выбрать направление"), handle_choose_direction))
    application.add_handler(MessageHandler(filters.Text("📊 Получить задачу"), handle_get_task))
    application.add_handler(MessageHandler(filters.Text("🛠️ Топ навыки"), handle_top_skills))
    application.add_handler(MessageHandler(filters.Text("📈 Статистика"), handle_statistics))

    application.add_handler(MessageHandler(filters.Text([
        "🐍 Python задачи", "🌐 Frontend задачи", "📊 Data Science задачи",
        "☕ Java задачи", "🔧 DevOps задачи", "🎲 Случайная задача"
    ]), handle_task_category))

    application.add_handler(MessageHandler(filters.Text([
        "🟢 Легкие задачи", "🟡 Средние задачи", "🔴 Сложные задачи", "🎲 Любая сложность"
    ]), handle_difficulty))

    application.add_handler(MessageHandler(filters.Text("👀 Показать решение"), handle_show_solution))
    application.add_handler(MessageHandler(filters.Text("✏️ Отправить решение"), handle_send_solution))  # NEW
    application.add_handler(MessageHandler(filters.Text("🔄 Новая задача"), handle_new_task))
    application.add_handler(MessageHandler(filters.Text("📊 Выбрать категорию"), handle_back_to_tasks))
    application.add_handler(MessageHandler(filters.Text("🔙 Главное меню"), handle_back_to_main))
    application.add_handler(MessageHandler(filters.Text("🔙 Назад к задачам"), handle_back_to_tasks))

    # NEW: обработчик текста для анализа (должен быть после всех точных совпадений)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_solution))


    logger.info("✅ Бот запущен с модулем анализа ошибок!")
    print("🤖 Бот запущен!")
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()