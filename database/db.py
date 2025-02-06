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
        # Преобразуем URL для PostgreSQL если нужно
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        self.engine = create_async_engine(url, echo=True)
        self.session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        async with self.session_maker() as session:
            return session

    async def init_default_users(self):
        """Инициализация базы данных начальными пользователями"""
        try:
            async with self.session_maker() as session:
                # Сначала очистим таблицу users
                await session.execute(text("DELETE FROM users"))
                
                for user_data in DEFAULT_USERS:
                    new_user = User(
                        telegram_id=user_data["telegram_id"],
                        username=user_data["username"],
                        full_name=user_data["full_name"],
                        is_admin=user_data["is_admin"]
                    )
                    session.add(new_user)
                
                await session.commit()
                
                # Проверим, что пользователи созданы
                result = await session.execute(text("SELECT * FROM users"))
                users = result.fetchall()
                print("Созданные пользователи:", users)
                
        except Exception as e:
            print(f"Ошибка при инициализации пользователей: {e}")

# Создаем глобальный экземпляр базы данных
from config import load_config
config = load_config()
db = Database(config.DATABASE_URL)

async def init_db():
    await db.init()
    await db.init_default_users()

# Создаем движок базы данных
engine = create_async_engine(
    "sqlite+aiosqlite:///bot.db",
    echo=True
)

# Создаем фабрику сессий
session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Функция для очистки базы данных
async def drop_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db()) 