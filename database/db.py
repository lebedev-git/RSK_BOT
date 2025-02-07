from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
import sys
import os

# Добавляем корневую директорию проекта в PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, User

DEFAULT_USERS = [
    {
        "telegram_id": 804636463,  # Добавляем ваш telegram_id
        "username": "lebedevrddm", 
        "full_name": "Лебедев Андрей", 
        "is_admin": True
    },
    {
        "telegram_id": None, 
        "username": "kolesnikova", 
        "full_name": "Колесникова Софья", 
        "is_admin": False
    },
    {
        "telegram_id": None, 
        "username": "omarov", 
        "full_name": "Омаров Игнат", 
        "is_admin": False
    },
]

class Database:
    def __init__(self, url: str):
        # Разные настройки для SQLite и PostgreSQL
        if url.startswith('sqlite'):
            self.engine = create_async_engine(
                url,
                echo=True
            )
        else:
            self.engine = create_async_engine(
                url,
                echo=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
        self.session_maker = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def init_default_users(self):
        try:
            async with self.session_maker() as session:
                # Проверяем существующих пользователей
                result = await session.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                
                if count == 0:  # Добавляем пользователей только если таблица пустая
                    for user_data in DEFAULT_USERS:
                        new_user = User(**user_data)
                        session.add(new_user)
                    
                    await session.commit()
                    print("Пользователи успешно добавлены")
                else:
                    print("Пользователи уже существуют")
                
        except Exception as e:
            print(f"Ошибка при инициализации пользователей: {e}")
            await session.rollback()

# Создаем глобальный экземпляр базы данных
from config import load_config
config = load_config()
db = Database(config.DATABASE_URL)

async def init_db():
    await db.init()
    await db.init_default_users()

# Функция для очистки базы данных
async def drop_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db()) 