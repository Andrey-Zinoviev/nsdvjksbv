import asyncpg
from psycopg2 import sql, connect
from datetime import datetime, timedelta
import aiofiles
from io import BytesIO

from config import *

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            host=DB_HOST,
            port=DB_PORT
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def fetch_brands(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch('SELECT brand_id, brand FROM brands')

    async def fetch_models(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch(
                'SELECT model_id, model, brand_id FROM models'
            )

    async def fetch_years(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch(
                'SELECT year_id, year, model_id FROM years'
                )

    async def fetch_files(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch(
                'SELECT column_id, photo, pdf, premium_photo, premium_pdf,\
                year_id FROM files'
            )

    async def fetch_premium_users(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch(
                'SELECT user_id, chat_id,\
                sub_start, sub_end, status FROM premium_users'
            )

    async def fetch_password(self):
        async with self.pool.acquire() as connection:
            return await connection.fetch(
                'SELECT password FROM password'
            )


# # # # # # # # # #
#   B R A N D S   #
# # # # # # # # # #
async def add_brand(brand_name: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'INSERT INTO brands (brand) VALUES ($1)'
        await conn.execute(query, brand_name)
        await conn.close()

        return f'Марка "{brand_name}" успешно добавлена!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def delete_brand(brand_name: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM brands WHERE brand = $1'
        await conn.execute(query, brand_name)
        await conn.close()

        return f'Марка "{brand_name}" успешно удалена!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def update_brand(old_brand: str, new_brand: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'UPDATE brands SET brand = $1 WHERE brand = $2'
        rows_affected = await conn.execute(query, new_brand, old_brand)
        await conn.close()

        if rows_affected:
            return f'Марка "{old_brand}" успешно обновлена на "{new_brand}"!'
        else:
            return f'Марка "{old_brand}" не найдена в базе данных.'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'


# # # # # # # # # #
#   M O D E L S   #
# # # # # # # # # #
async def add_model(model_name: str, chat_id: int):
    try:
        from .handlers import brand_ids
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'INSERT INTO models (model, brand_id)\
        VALUES ($1, $2)'
        await conn.execute(
            query, model_name, brand_ids[chat_id]
        )
        await conn.close()

        return f'Модель "{model_name}" успешно добавлена!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def delete_model(model_name: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM models WHERE model = $1'
        await conn.execute(query, model_name)
        await conn.close()

        return f'Модель "{model_name}" успешно удалена!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def update_model(old_model: str, new_model: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'UPDATE models SET model = $1 WHERE model = $2'
        rows_affected = await conn.execute(query, new_model, old_model)
        await conn.close()

        if rows_affected:
            return f'Модель "{old_model}" успешно обновлена на "{new_model}"!'
        else:
            return f'Модель "{old_model}" не найдена в базе данных.'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

# # # # # # # # #
#   Y E A R S   #
# # # # # # # # #
async def add_year(year_name: str, chat_id: int):
    try:
        from .handlers import model_ids, models, brands
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'INSERT INTO years (year, model_id, model, brand)\
        VALUES ($1, $2, $3, $4)'
        await conn.execute(
            query, year_name,
            model_ids[chat_id], models[chat_id],
            brands[chat_id]
        )
        await conn.close()

        return f'Год "{year_name}" успешно добавлен!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def delete_year(year_name: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM years WHERE year = $1'
        await conn.execute(query, year_name)
        await conn.close()

        return f'Год "{year_name}" успешно удален!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def update_year(old_year: str, new_year: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'UPDATE years SET year = $1 WHERE year = $2'

        rows_affected = await conn.execute(query, new_year, old_year)
        await conn.close()

        if rows_affected:
            return f'Год "{old_year}" успешно обновлен на "{new_year}"!'
        else:
            return f'Год "{old_year}" не найден в базе данных.'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

# # # # # # # # #
#   P H O T O   #
# # # # # # # # #
async def add_photo(photo_way: str, chat_id: int):
    try:
        from .handlers import year_ids, years, models, brands
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        INSERT INTO files (photo, year_id, year, model, brand)
        VALUES ($1, $2, $3, $4, $5);
        """
        await conn.execute(
            query, photo_way,
            year_ids[chat_id], years[chat_id],
            models[chat_id], brands[chat_id]
        )
        await conn.close()

        return f'Фото успешно добавлено!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

async def delete_photo(column_id: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM files WHERE column_id = $1'
        await conn.execute(query, int(column_id))
        await conn.close()

        return f'Фото успешно удалено!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

# # # # # # # # # # # # # # # # #
#   P R E M I U M   P H O T O   #
# # # # # # # # # # # # # # # # #
async def add_premium_photo(premium_photo_way: str, chat_id: int):
    try:
        from .handlers import year_ids, years, models, brands
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        INSERT INTO files (premium_photo, year_id, year, model, brand)
        VALUES ($1, $2, $3, $4, $5);
        """
        await conn.execute(
            query, premium_photo_way,
            year_ids[chat_id], years[chat_id],
            models[chat_id], brands[chat_id]
        )
        await conn.close()

        return f'Фото успешно добавлено!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

async def delete_premium_photo(column_id: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM files WHERE column_id = $1'
        await conn.execute(query, int(column_id))
        await conn.close()

        return f'Премиальное фото успешно удалено!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

# # # # # # #
#   P D F   #
# # # # # # #
async def add_pdf(pdf_way: str, chat_id: int):
    try:
        from .handlers import year_ids, years, models, brands
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        INSERT INTO files (pdf, year_id, year, model, brand)
        VALUES ($1, $2, $3, $4, $5);
        """
        await conn.execute(
            query, pdf_way,
            year_ids[chat_id], years[chat_id],
            models[chat_id], brands[chat_id]
        )
        await conn.close()

        return f'Файл успешно добавлен!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

async def delete_pdf(column_id: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM files WHERE column_id = $1'
        await conn.execute(query, int(column_id))
        await conn.close()

        return f'Файл успешно удалено!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'

# # # # # # # # # # # # # # #
#   P R E M I U M   P D F   #
# # # # # # # # # # # # # # #
async def add_premium_pdf(premium_pdf_way: str, chat_id: int):
    try:
        from .handlers import year_ids, years, models, brands
        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        INSERT INTO files (premium_pdf, year_id, year, model, brand)
        VALUES ($1, $2, $3, $4, $5);
        """
        await conn.execute(
            query, premium_pdf_way,
            year_ids[chat_id], years[chat_id],
            models[chat_id], brands[chat_id]
        )
        await conn.close()

        return f'Премиальный файл успешно добавлен!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

async def delete_premium_pdf(column_id: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM files WHERE column_id = $1'
        await conn.execute(query, int(column_id))
        await conn.close()

        return f'Премиальный файл успешно удален!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

# # # # # # # # #
#   U S E R S   #
# # # # # # # # #
async def add_premium_user(chat_id: str):
    try:
        sub_start = datetime.now()
        sub_end = sub_start + timedelta(days=30)
        sub_start = sub_start.strftime('%Y-%m-%d %H:%M:%S')
        sub_end = sub_end.strftime('%Y-%m-%d %H:%M:%S')
        print('Дата начала подписки:', sub_start)
        print('Дата окончания подписки:', sub_end)

        conn = await asyncpg.connect(DATABASE_URL)
        query = """
        INSERT INTO premium_users (chat_id, sub_start, sub_end, status)
        VALUES ($1, $2, $3, $4);
        """
        await conn.execute(query, chat_id, sub_start, sub_end, 'active')
        await conn.close()

        return f'Вы успешно получили премиум подписку!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

async def delete_premium_user(chat_id: str):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'DELETE FROM premium_users WHERE chat_id = $1'
        await conn.execute(query, chat_id)
        await conn.close()
        return f'Ваша премиум подписка истекла!'
        
    except Exception as e:
        return f'Упс! Произошла ошибка: {e}'

# # # # # # # # # # # #
#   P A S S W O R D   #
# # # # # # # # # # # #
async def update_password(new_pass: str):
    try:
        from .handlers import db
        pass_row = await db.fetch_password()
        old_pass = pass_row[0]['password']
        conn = await asyncpg.connect(DATABASE_URL)
        query = 'UPDATE password SET password = $1 WHERE password = $2'

        await conn.execute(query, new_pass, old_pass)
        await conn.close()

        return f'Успешно!'
        
    except Exception as e:
        return f'Произошла ошибка: {e}'