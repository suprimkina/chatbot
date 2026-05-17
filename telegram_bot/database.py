import aiosqlite
from telegram_bot.config import DATABASE_PATH


class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH

    async def get_connection(self):
        """Получение подключения к базе данных"""
        return await aiosqlite.connect(self.db_path)

    async def get_specializations(self):
        """Получение списка всех направлений"""
        conn = await self.get_connection()
        cursor = await conn.cursor()

        await cursor.execute("SELECT id, name FROM specializations")
        specializations = await cursor.fetchall()

        await conn.close()
        return specializations

    async def get_tasks_by_specialization(self, specialization_id, difficulty=None, limit=5):
        """Получение задач по направлению и сложности"""
        conn = await self.get_connection()
        cursor = await conn.cursor()

        if difficulty:
            await cursor.execute('''
                SELECT id, title, description, difficulty, solution, source_url
                FROM interview_tasks 
                WHERE specialization_id = ? AND difficulty = ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (specialization_id, difficulty, limit))
        else:
            await cursor.execute('''
                SELECT id, title, description, difficulty, solution, source_url
                FROM interview_tasks 
                WHERE specialization_id = ?
                ORDER BY RANDOM()
                LIMIT ?
            ''', (specialization_id, limit))

        tasks = await cursor.fetchall()
        await conn.close()
        return tasks

    async def get_top_skills(self, specialization_id, limit=10):
        """Получение топ навыков для направления"""
        conn = await self.get_connection()
        cursor = await conn.cursor()

        await cursor.execute('''
            SELECT s.name, COUNT(vs.skill_id) as demand_count
            FROM vacancy_skills vs
            JOIN vacancies v ON vs.vacancy_id = v.id
            JOIN skills s ON vs.skill_id = s.id
            WHERE v.specialization_id = ?
            GROUP BY s.id, s.name
            ORDER BY demand_count DESC
            LIMIT ?
        ''', (specialization_id, limit))

        skills = await cursor.fetchall()
        await conn.close()
        return skills

    async def get_vacancies_stats(self, specialization_id):
        """Получение статистики по вакансиям"""
        conn = await self.get_connection()
        cursor = await conn.cursor()

        await cursor.execute('''
            SELECT 
                COUNT(*) as total_vacancies,
                AVG(salary_min) as avg_min_salary,
                AVG(salary_max) as avg_max_salary,
                level,
                COUNT(*) as level_count
            FROM vacancies
            WHERE specialization_id = ?
            GROUP BY level
        ''', (specialization_id,))

        stats = await cursor.fetchall()
        await conn.close()
        return stats


# Создаем глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()