from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram_bot.database import db_manager


async def choose_specialization(update: Update, context: CallbackContext):
    """Обработчик выбора направления"""
    specializations = await db_manager.get_specializations()

    if not specializations:
        await update.message.reply_text("❌ В базе данных пока нет направлений")
        return

    # Создаем инлайн-клавиатуру с направлениями
    keyboard = []
    for spec_id, spec_name in specializations:
        keyboard.append([InlineKeyboardButton(spec_name, callback_data=f"spec_{spec_id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎯 <b>Выбери направление для подготовки:</b>",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_specialization_choice(update: Update, context: CallbackContext):
    """Обработчик выбора конкретного направления"""
    query = update.callback_query
    await query.answer()

    specialization_id = int(query.data.replace("spec_", ""))
    context.user_data['current_specialization'] = specialization_id

    # Получаем название направления
    specializations = await db_manager.get_specializations()
    spec_name = next((name for id, name in specializations if id == specialization_id), "Неизвестно")

    # Создаем клавиатуру для выбора сложности
    keyboard = [
        [
            InlineKeyboardButton("🟢 Легкие", callback_data=f"diff_{specialization_id}_easy"),
            InlineKeyboardButton("🟡 Средние", callback_data=f"diff_{specialization_id}_medium"),
        ],
        [
            InlineKeyboardButton("🔴 Сложные", callback_data=f"diff_{specialization_id}_hard"),
            InlineKeyboardButton("🎲 Случайные", callback_data=f"diff_{specialization_id}_random"),
        ],
        [
            InlineKeyboardButton("🛠️ Топ навыки", callback_data=f"skills_{specialization_id}"),
            InlineKeyboardButton("📈 Статистика", callback_data=f"stats_{specialization_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"🎯 <b>Выбрано:</b> {spec_name}\n\n"
        "Теперь выбери сложность задач или посмотри статистику:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def handle_difficulty_choice(update: Update, context: CallbackContext):
    """Обработчик выбора сложности задач"""
    query = update.callback_query
    await query.answer()

    # Парсим данные из callback
    _, specialization_id, difficulty = query.data.split("_")
    specialization_id = int(specialization_id)

    # Получаем задачи
    if difficulty == 'random':
        tasks = await db_manager.get_tasks_by_specialization(specialization_id, limit=3)
    else:
        tasks = await db_manager.get_tasks_by_specialization(specialization_id, difficulty, limit=3)

    if not tasks:
        await query.edit_message_text(
            "❌ По выбранным критериям задач пока нет.\n"
            "Попробуй выбрать другую сложность или направление."
        )
        return

    # Отправляем задачи
    for task in tasks:
        task_id, title, description, task_difficulty, solution, source_url = task

        # Формируем сообщение с задачей
        task_text = f"""
📝 <b>{title}</b>
📊 Сложность: {task_difficulty}

<b>Задача:</b>
{description}
        """

        if source_url:
            task_text += f"\n🔗 <a href='{source_url}'>Источник</a>"

        # Если есть решение, добавляем кнопку для его показа
        if solution:
            keyboard = [[InlineKeyboardButton("👀 Показать решение", callback_data=f"solution_{task_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reply_markup = None

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=task_text,
            reply_markup=reply_markup,
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    # Добавляем кнопку для получения новых задач
    keyboard = [[InlineKeyboardButton("🔄 Новые задачи", callback_data=f"spec_{specialization_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Хочешь получить еще задачи?",
        reply_markup=reply_markup
    )


async def handle_solution_request(update: Update, context: CallbackContext):
    """Обработчик запроса решения задачи"""
    query = update.callback_query
    await query.answer()

    task_id = int(query.data.replace("solution_", ""))

    # Получаем решение из базы данных
    conn = await db_manager.get_connection()
    cursor = await conn.cursor()
    await cursor.execute("SELECT title, solution FROM interview_tasks WHERE id = ?", (task_id,))
    task = await cursor.fetchone()
    await conn.close()

    if task and task[1]:
        title, solution = task
        response = f"""
✅ <b>Решение задачи:</b> {title}

{solution}

💡 <i>Попробуй решить задачу самостоятельно перед просмотром решения!</i>
        """
    else:
        response = "❌ Решение для этой задачи пока не добавлено."

    await query.edit_message_text(response, parse_mode='HTML')


async def handle_skills_request(update: Update, context: CallbackContext):
    """Обработчик запроса топ навыков"""
    query = update.callback_query
    await query.answer()

    specialization_id = int(query.data.replace("skills_", ""))

    skills = await db_manager.get_top_skills(specialization_id)

    if not skills:
        await query.edit_message_text("❌ Нет данных о навыках для этого направления")
        return

    # Формируем сообщение со списком навыков
    skills_text = "🛠️ <b>Топ востребованных навыков:</b>\n\n"

    for i, (skill_name, demand_count) in enumerate(skills, 1):
        skills_text += f"{i}. {skill_name} - <b>{demand_count}</b> упоминаний\n"

    skills_text += "\n💡 <i>Обрати внимание на эти технологии при подготовке!</i>"

    await query.edit_message_text(skills_text, parse_mode='HTML')


async def handle_stats_request(update: Update, context: CallbackContext):
    """Обработчик запроса статистики"""
    query = update.callback_query
    await query.answer()

    specialization_id = int(query.data.replace("stats_", ""))

    stats = await db_manager.get_vacancies_stats(specialization_id)
    specializations = await db_manager.get_specializations()
    spec_name = next((name for id, name in specializations if id == specialization_id), "Неизвестно")

    if not stats:
        await query.edit_message_text("❌ Нет статистики для этого направления")
        return

    # Формируем сообщение со статистикой
    stats_text = f"📈 <b>Статистика по направлению:</b> {spec_name}\n\n"

    total_vacancies = 0
    salary_data = []

    for row in stats:
        total, avg_min, avg_max, level, level_count = row
        total_vacancies += level_count

        if avg_min and avg_max:
            salary_info = f"💵 {int(avg_min or 0):,} - {int(avg_max or 0):,} руб."
        else:
            salary_info = "💵 Зарплата не указана"

        stats_text += f"• <b>{level}</b>: {level_count} вакансий\n  {salary_info}\n\n"

    stats_text += f"📊 <b>Всего вакансий:</b> {total_vacancies}"

    await query.edit_message_text(stats_text, parse_mode='HTML')