import asyncio
import os
from database.db import db, init_db

async def reset_database():
    # Удаляем существующую базу данных
    if os.path.exists("bot_database.db"):
        os.remove("bot_database.db")
        print("Существующая база данных удалена")
    
    # Инициализируем базу заново
    await init_db()
    print("База данных создана заново")

if __name__ == '__main__':
    asyncio.run(reset_database()) 