import asyncio
from database.db import db
from sqlalchemy import text

async def setup_admin():
    try:
        async with db.session_maker() as session:
            # Сначала проверим текущее состояние
            check_query = text("SELECT * FROM users")
            result = await session.execute(check_query)
            users = result.fetchall()
            print("\nТекущие пользователи:")
            for user in users:
                print(user)
            
            # Устанавливаем права администратора
            query = text("""
                UPDATE users 
                SET is_admin = true,
                    telegram_id = :telegram_id
                WHERE full_name = 'Лебедев Андрей'
                RETURNING id, full_name, is_admin, telegram_id
            """)
            result = await session.execute(query, {"telegram_id": 804636463})
            updated_user = result.first()
            await session.commit()
            
            if updated_user:
                print(f"\nОбновлен пользователь: {updated_user}")
            else:
                print("\nОшибка: пользователь не найден или не обновлен")
            
            # Проверяем финальный результат
            final_query = text("SELECT * FROM users")
            result = await session.execute(final_query)
            users = result.fetchall()
            print("\nФинальное состояние пользователей:")
            for user in users:
                print(user)
            
    except Exception as e:
        print(f"Ошибка при установке прав администратора: {e}")
        raise e

if __name__ == '__main__':
    asyncio.run(setup_admin()) 