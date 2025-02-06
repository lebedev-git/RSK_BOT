from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram import flags, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import db
from database.models import User, Attendance
from datetime import datetime
import pytz
from sqlalchemy import text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from calendar import monthrange
from datetime import timedelta
from config import load_config
from aiogram.exceptions import TelegramBadRequest
from services.ai_service import get_ai_response

async def generate_presence_table(date: datetime.date) -> str:
    """Генерирует таблицу присутствия на указанную дату"""
    try:
        async with db.session_maker() as session:
            today_start = datetime.combine(date, datetime.min.time())
            today_end = datetime.combine(date, datetime.max.time())
            
            # Получаем всех пользователей и их последний статус за сегодня
            query = text("""
                WITH LastStatus AS (
                    SELECT user_id, status,
                           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date DESC) as rn
                    FROM attendance
                    WHERE date BETWEEN :start AND :end
                )
                SELECT u.full_name, ls.status
                FROM users u
                LEFT JOIN LastStatus ls ON u.id = ls.user_id AND ls.rn = 1
                ORDER BY u.full_name
            """)
            
            result = await session.execute(query, {
                'start': today_start,
                'end': today_end
            })
            
            rows = result.fetchall()
            present_users = []
            absent_users = []
            excused_users = []
            
            for row in rows:
                name = row[0]
                status = row[1]
                
                if status == 'present':
                    present_users.append(name)
                elif status == 'excused':
                    excused_users.append(name)
                else:
                    absent_users.append(name)
            
            # Формируем отчет
            table = "Присутствие на созвоне:\n\n"
            
            table += "✅ Присутствуют:\n"
            if present_users:
                for user in present_users:
                    table += f"- {user}\n"
            else:
                table += "Никто не отметился как присутствующий\n"
            
            table += "\n❌ Отсутствуют:\n"
            if absent_users:
                for user in absent_users:
                    table += f"- {user}\n"
            else:
                table += "Все присутствуют\n"
            
            if excused_users:
                table += "\n⚠️ Отсутствуют по уважительной причине:\n"
                for user in excused_users:
                    table += f"- {user}\n"
            
            return table
            
    except Exception as e:
        print(f"Ошибка при генерации таблицы: {e}")
        return "Ошибка при формировании отчета"

@flags.chat_action("typing")
async def send_report(bot: Bot, group_chat_id: str):
    """Отправляет отчет в групповой чат"""
    try:
        today = datetime.now(pytz.timezone('Europe/Moscow')).date()
        report = await generate_presence_table(today)
        
        message_text = f"Отчет о присутствии на {today}:\n\n{report}"
        
        await bot.send_message(
            group_chat_id,
            message_text,
            parse_mode=None  # Отключаем парсинг разметки
        )
        print("Отчет успешно отправлен в группу!")
    except Exception as e:
        print(f"Ошибка отправки отчета в группу: {e}")

# Обработчик команды /report
async def cmd_report(message: types.Message):
    """Команда для получения отчета о присутствии"""
    try:
        today = datetime.now(pytz.timezone('Europe/Moscow')).date()
        report = await generate_presence_table(today)
        
        # Подготавливаем сообщение без форматирования
        base_message = f"Отчет о присутствии на {today}:\n\n{report}"
        
        # Экранируем специальные символы для MarkdownV2
        escaped_message = base_message
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            escaped_message = escaped_message.replace(char, f'\\{char}')
        
        # Отправляем сообщение без парсинга разметки
        await message.answer(escaped_message)
        
    except Exception as e:
        print(f"Ошибка при выполнении команды report: {e}")
        await message.answer("Произошла ошибка при формировании отчета")

class AdminStates(StatesGroup):
    choosing_action = State()
    marking_attendance = State()
    choosing_month = State()

async def cmd_admin(message: types.Message, state: FSMContext):
    """Обработчик команды /admin"""
    try:
        async with db.session_maker() as session:
            # Проверяем права администратора
            query = text("SELECT is_admin FROM users WHERE telegram_id = :telegram_id")
            result = await session.execute(query, {"telegram_id": message.from_user.id})
            user = result.first()
            
            if not user or not user[0]:
                await message.answer("У вас нет прав администратора")
                return
            
            # Создаем клавиатуру для админ-панели со всеми пунктами
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📝 Отметить присутствие", callback_data="admin:attendance")
            keyboard.button(text="📊 Выгрузка статистики", callback_data="admin:stats")
            keyboard.button(text="👥 Управление администраторами", callback_data="admin:manage_admins")
            keyboard.adjust(1)
            
            await message.answer(
                "👨‍💼 Панель администратора\n\n"
                "Выберите действие:",
                reply_markup=keyboard.as_markup()
            )
            await state.set_state(AdminStates.choosing_action)
            
    except Exception as e:
        print(f"Ошибка в cmd_admin: {e}")
        await message.answer("Произошла ошибка при обработке команды")

async def process_admin_callback(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    
    if action == "back":
        async with db.session_maker() as session:
            # Проверяем, все ли отмечены
            today = datetime.now(pytz.timezone('Europe/Moscow'))
            check_query = text("""
                WITH UserCount AS (
                    SELECT COUNT(*) as total FROM users
                ),
                MarkedCount AS (
                    SELECT COUNT(DISTINCT user_id) as marked 
                    FROM attendance 
                    WHERE DATE(date) = DATE(:today)
                )
                SELECT u.total, COALESCE(m.marked, 0) as marked
                FROM UserCount u
                LEFT JOIN MarkedCount m ON 1=1
            """)
            result = await session.execute(check_query, {"today": today})
            total, marked = result.first()
            
            if total > marked and await state.get_state() == AdminStates.marking_attendance:
                await callback.answer(
                    f"Пожалуйста, отметьте всех пользователей ({marked} из {total})", 
                    show_alert=True
                )
                return
        
        # Возвращаемся в главное меню админа
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📝 Отметить присутствие", callback_data="admin:attendance")
        keyboard.button(text="📊 Выгрузка статистики", callback_data="admin:stats")
        keyboard.button(text="👥 Управление администраторами", callback_data="admin:manage_admins")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            "👨‍💼 Панель администратора\n\n"
            "Выберите действие:",
            reply_markup=keyboard.as_markup()
        )
        await state.set_state(AdminStates.choosing_action)
        
    elif action == "attendance":
        await update_attendance_list(callback)

    elif action == "manage_admins":
        # Показываем список пользователей с их админ-статусом
        keyboard = InlineKeyboardBuilder()
        
        async with db.session_maker() as session:
            query = text("""
                SELECT id, full_name, is_admin 
                FROM users 
                ORDER BY full_name
            """)
            result = await session.execute(query)
            users = result.fetchall()
            
            for user in users:
                admin_status = "✅" if user[2] else "❌"
                keyboard.button(
                    text=f"{admin_status} {user[1]}", 
                    callback_data=f"toggle_admin:{user[0]}:{not user[2]}"
                )
            
            keyboard.button(text="🔙 Назад", callback_data="admin:back")
            keyboard.adjust(1)
        
        await callback.message.edit_text(
            "Управление правами администраторов\n"
            "Нажмите на пользователя, чтобы изменить его права:",
            reply_markup=keyboard.as_markup()
        )

    elif action == "stats":
        keyboard = InlineKeyboardBuilder()
        current_date = datetime.now()
        
        # Показываем последние 3 месяца
        for i in range(3):
            date = current_date - timedelta(days=30*i)
            month_name = date.strftime("%B %Y")
            keyboard.button(
                text=month_name,
                callback_data=f"stats_month:{date.strftime('%Y-%m')}"
            )
        
        keyboard.button(text="🔙 Назад", callback_data="admin:back")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            "Выберите месяц для просмотра статистики:",
            reply_markup=keyboard.as_markup()
        )

# Добавим обработчик для статистики
async def process_stats_callback(callback: CallbackQuery, state: FSMContext):
    try:
        _, date_str = callback.data.split(":")
        year, month = map(int, date_str.split("-"))
        
        # Генерируем статистику
        stats = await generate_monthly_stats(year, month)
        
        # Создаем клавиатуру для возврата
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 Назад", callback_data="admin:stats")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            stats,
            reply_markup=keyboard.as_markup()
        )
        
    except Exception as e:
        print(f"Ошибка при обработке статистики: {e}")
        await callback.answer("Произошла ошибка при формировании статистики", show_alert=True)

# И добавим новый обработчик для выбора месяца:
async def process_stats_month_callback(callback: CallbackQuery, state: FSMContext):
    try:
        _, date_str = callback.data.split(":")
        year, month = map(int, date_str.split("-"))
        
        stats = await generate_monthly_stats(year, month)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 Назад", callback_data="admin:stats")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            stats,
            reply_markup=keyboard.as_markup()
        )
    except Exception as e:
        print(f"Ошибка при формировании статистики: {e}")
        await callback.answer("Ошибка при формировании статистики", show_alert=True)

# Обновим регистрацию обработчиков
def register_admin_handlers(dp: Dispatcher):
    dp.message.register(cmd_admin, Command("admin"))
    dp.callback_query.register(process_admin_callback, lambda c: c.data.startswith("admin:"))
    dp.callback_query.register(process_stats_month_callback, lambda c: c.data.startswith("stats_month:"))
    dp.callback_query.register(process_status_callback, lambda c: c.data.startswith("status:"))
    dp.callback_query.register(process_toggle_admin, lambda c: c.data.startswith("toggle_admin:"))

async def generate_monthly_stats(year: int, month: int) -> str:
    try:
        async with db.session_maker() as session:
            start_date = datetime(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = datetime(year, month, last_day, 23, 59, 59)
            
            query = text("""
                SELECT 
                    u.full_name,
                    COUNT(CASE WHEN a.status = 'present' THEN 1 END) as present_count,
                    COUNT(CASE WHEN a.status = 'absent' THEN 1 END) as absent_count,
                    COUNT(CASE WHEN a.status = 'excused' THEN 1 END) as excused_count
                FROM users u
                LEFT JOIN attendance a ON u.id = a.user_id 
                AND a.date BETWEEN :start AND :end
                GROUP BY u.id, u.full_name
                ORDER BY u.full_name
            """)
            
            result = await session.execute(query, {
                'start': start_date,
                'end': end_date
            })
            
            stats = f"📊 Статистика за {start_date.strftime('%B %Y')}:\n\n"
            
            for row in result:
                stats += f"👤 {row[0]}:\n"
                stats += f"   ✅ Присутствий: {row[1]}\n"
                stats += f"   ❌ Отсутствий: {row[2]}\n"
                stats += f"   ⚠️ Уважительных причин: {row[3]}\n\n"
            
            return stats
            
    except Exception as e:
        print(f"Ошибка при генерации статистики: {e}")
        return "Ошибка при формировании статистики"

async def update_attendance_list(callback: CallbackQuery):
    """Обновляет список пользователей для отметки присутствия"""
    keyboard = InlineKeyboardBuilder()
    
    async with db.session_maker() as session:
        query = text("""
            SELECT u.id, u.full_name, 
                (SELECT a.status 
                 FROM attendance a 
                 WHERE a.user_id = u.id 
                 AND DATE(a.date) = DATE(:today)
                 ORDER BY a.date DESC 
                 LIMIT 1) as status
            FROM users u
            ORDER BY u.full_name
        """)
        result = await session.execute(query, {
            'today': datetime.now(pytz.timezone('Europe/Moscow'))
        })
        users = result.fetchall()
        
        buttons = []
        # Для каждого пользователя создаем группу кнопок
        for user in users:
            user_id, name = user[0], user[1]
            
            # Добавляем имя как неактивную кнопку
            buttons.append([{
                "text": f"👤 {name}",
                "callback_data": f"header:{user_id}"
            }])
            
            # Добавляем ряд с тремя кнопками статуса
            buttons.append([
                {"text": "✅", "callback_data": f"status:{user_id}:present"},
                {"text": "❌", "callback_data": f"status:{user_id}:absent"},
                {"text": "⚠️", "callback_data": f"status:{user_id}:excused"}
            ])
        
        # Добавляем кнопку "Назад"
        buttons.append([{
            "text": "🔙 Назад",
            "callback_data": "admin:back"
        }])
        
        # Создаем клавиатуру из подготовленных кнопок
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        "Отметьте присутствие для каждого участника:",
        reply_markup=keyboard
    )

async def process_status_callback(callback: CallbackQuery, state: FSMContext):
    try:
        _, user_id, status = callback.data.split(":")
        
        async with db.session_maker() as session:
            if not await check_admin_rights(session, callback.from_user.id):
                await callback.answer("У вас нет прав администратора", show_alert=True)
                return
            
            today = datetime.now(pytz.timezone('Europe/Moscow'))
            
            # 1. Сохраняем отметку
            delete_query = text("""
                DELETE FROM attendance 
                WHERE user_id = :user_id 
                AND DATE(date) = DATE(:today)
            """)
            await session.execute(delete_query, {
                "user_id": user_id,
                "today": today
            })
            
            attendance = Attendance(
                user_id=int(user_id),
                date=today,
                status=status
            )
            session.add(attendance)
            await session.commit()
            
            # 2. Проверяем количество отмеченных пользователей
            check_query = text("""
                WITH UserCount AS (
                    SELECT COUNT(*) as total FROM users
                ),
                MarkedUsers AS (
                    SELECT DISTINCT user_id 
                    FROM attendance 
                    WHERE DATE(date) = DATE(:today)
                )
                SELECT 
                    (SELECT total FROM UserCount) as total,
                    (SELECT COUNT(*) FROM MarkedUsers) as marked
            """)
            result = await session.execute(check_query, {"today": today})
            total, marked = result.first()
            
            # 3. Получаем текущий статус всех пользователей для обновления списка
            status_query = text("""
                SELECT u.id, u.full_name, 
                    (SELECT status 
                     FROM attendance a 
                     WHERE a.user_id = u.id 
                     AND DATE(a.date) = DATE(:today)
                     ORDER BY a.date DESC
                     LIMIT 1) as status
                FROM users u
                ORDER BY u.full_name
            """)
            users = await session.execute(status_query, {"today": today})
            users = users.fetchall()
            
            # 4. Если все отмечены - отправляем отчет и возвращаемся в меню
            if total == marked:
                config = load_config()
                await send_report(callback.bot, config.GROUP_CHAT_ID)
                
                admin_keyboard = InlineKeyboardBuilder()
                admin_keyboard.button(text="📝 Отметить присутствие", callback_data="admin:attendance")
                admin_keyboard.button(text="📊 Выгрузка статистики", callback_data="admin:stats")
                admin_keyboard.button(text="👥 Управление администраторами", callback_data="admin:manage_admins")
                admin_keyboard.adjust(1)
                
                await callback.message.edit_text(
                    "👨‍💼 Панель администратора\n\n"
                    "Выберите действие:",
                    reply_markup=admin_keyboard.as_markup()
                )
                await state.set_state(AdminStates.choosing_action)
            else:
                # 5. Иначе обновляем список с текущими статусами
                buttons = []
                for user in users:
                    user_id, name, current_status = user
                    status_icon = "✅" if current_status == "present" else "❌" if current_status == "absent" else "⚠️" if current_status == "excused" else "❔"
                    
                    buttons.append([{
                        "text": f"{status_icon} {name}",
                        "callback_data": f"header:{user_id}"
                    }])
                    buttons.append([
                        {"text": "✅", "callback_data": f"status:{user_id}:present"},
                        {"text": "❌", "callback_data": f"status:{user_id}:absent"},
                        {"text": "⚠️", "callback_data": f"status:{user_id}:excused"}
                    ])
                
                buttons.append([{"text": "🔙 Назад", "callback_data": "admin:back"}])
                keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
                
                try:
                    await callback.message.edit_text(
                        f"Отметьте присутствие для каждого участника: (отмечено {marked} из {total})",
                        reply_markup=keyboard
                    )
                except TelegramBadRequest as e:
                    if "message is not modified" not in str(e):
                        raise
            
            await callback.answer()
            
    except Exception as e:
        print(f"Ошибка при установке статуса: {str(e)}")
        await callback.answer(f"Произошла ошибка: {str(e)}", show_alert=True)

async def process_toggle_admin(callback: CallbackQuery, state: FSMContext):
    """Обработчик для переключения админских прав"""
    try:
        _, user_id, new_status = callback.data.split(":")
        new_status = new_status.lower() == 'true'
        
        async with db.session_maker() as session:
            # Проверяем права текущего пользователя
            admin_query = text("SELECT is_admin FROM users WHERE telegram_id = :telegram_id")
            result = await session.execute(admin_query, {"telegram_id": callback.from_user.id})
            admin = result.first()
            
            if not admin or not admin[0]:
                await callback.answer("У вас нет прав администратора", show_alert=True)
                return
            
            # Получаем имя пользователя, которому меняем права
            name_query = text("SELECT full_name FROM users WHERE id = :user_id")
            result = await session.execute(name_query, {"user_id": user_id})
            user = result.first()
            
            if not user:
                await callback.answer("Пользователь не найден", show_alert=True)
                return
            
            # Обновляем статус администратора
            update_query = text("""
                UPDATE users 
                SET is_admin = :is_admin 
                WHERE id = :user_id
            """)
            await session.execute(update_query, {
                "is_admin": new_status,
                "user_id": user_id
            })
            await session.commit()
            
            status_text = "назначен администратором" if new_status else "снят с прав администратора"
            await callback.answer(
                f"Пользователь {user[0]} {status_text}",
                show_alert=True
            )
            
            # Обновляем список администраторов
            await process_admin_callback(callback, state)
            
    except Exception as e:
        print(f"Ошибка при изменении прав администратора: {e}")
        await callback.answer(
            "Произошла ошибка при изменении прав администратора",
            show_alert=True
        )

async def check_admin_rights(session, telegram_id: int) -> bool:
    """Проверка прав администратора"""
    query = text("SELECT is_admin FROM users WHERE telegram_id = :telegram_id")
    result = await session.execute(query, {"telegram_id": telegram_id})
    user = result.first()
    return bool(user and user[0])

async def handle_message(message: types.Message):
    """Обработчик всех текстовых сообщений"""
    try:
        # Показываем, что бот печатает
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        # Получаем ответ от AI
        response = await get_ai_response(message.text)
        
        # Если ответ содержит сообщение об ошибке, добавляем контактную информацию
        if "Извините, " in response:
            response += "\n\nЕсли проблема повторяется, пожалуйста, сообщите администратору."
        
        # Отправляем ответ
        await message.answer(response)
    except Exception as e:
        print(f"Ошибка при обработке сообщения: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке сообщения.\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )

def register_handlers(dp: Dispatcher):
    # Регистрируем обработчики команд
    dp.message.register(cmd_admin, Command("admin"))
    dp.message.register(cmd_report, Command("report"))
    
    # Регистрируем обработчик для всех остальных текстовых сообщений
    # Важно: регистрируем последним, чтобы он не перехватывал команды
    dp.message.register(handle_message, F.text & ~F.command)

def register_admin_handlers(dp: Dispatcher):
    # Регистрируем админские обработчики для callback
    dp.callback_query.register(process_admin_callback, lambda c: c.data.startswith("admin:"))
    dp.callback_query.register(process_stats_month_callback, lambda c: c.data.startswith("stats_month:"))
    dp.callback_query.register(process_status_callback, lambda c: c.data.startswith("status:"))
    dp.callback_query.register(process_toggle_admin, lambda c: c.data.startswith("toggle_admin:"))