from datetime import datetime, time, timedelta
from config import load_config
from handlers import send_report, cmd_report, register_handlers, register_admin_handlers
from database.db import init_db
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import os

# Загружаем конфигурацию
config = load_config()

# Инициализируем бота и диспетчер
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Инициализируем планировщик
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))

async def setup_scheduler():
    """Настройка планировщика задач"""
    try:
        # Конвертируем строки времени в объекты time
        morning_time = datetime.strptime(config.MORNING_REPORT_TIME, "%H:%M").time()
        evening_time = datetime.strptime(config.EVENING_REPORT_TIME, "%H:%M").time()
        
        # Планируем отправку отчетов
        scheduler.add_job(
            send_report,
            trigger='cron',
            hour=morning_time.hour,
            minute=morning_time.minute,
            args=[bot, config.GROUP_CHAT_ID]
        )
        
        scheduler.add_job(
            send_report,
            trigger='cron',
            hour=evening_time.hour,
            minute=evening_time.minute,
            args=[bot, config.GROUP_CHAT_ID]
        )
        
        # Запускаем планировщик
        scheduler.start()
            
    except Exception as e:
        print(f"Ошибка в планировщике: {e}")

async def on_startup():
    """Действия при запуске бота"""
    try:
        # Инициализируем базу данных
        await init_db()
        print("База данных инициализирована")
        
        # Настраиваем и запускаем планировщик
        await setup_scheduler()
        print("Планировщик настроен")
        
    except Exception as e:
        print(f"Ошибка при запуске: {e}")

async def main():
    """Основная функция для запуска бота"""
    try:
        # Регистрируем обработчики
        register_handlers(dp)
        register_admin_handlers(dp)
        
        # Выполняем действия при запуске
        await on_startup()
        
        # Запускаем бота
        print("Бот запущен")
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
        scheduler.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен") 