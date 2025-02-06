import aiosqlite

DB_NAME = "presence.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS presence (
                user_id INTEGER,
                date DATE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        await db.commit()

# Получение ID пользователя по имени
async def get_user_id(name):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM users WHERE name = ?", (name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                # Если пользователя нет, добавляем его
                await db.execute("INSERT INTO users (name) VALUES (?)", (name,))
                await db.commit()
                async with db.execute("SELECT id FROM users WHERE name = ?", (name,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        return None

# Проверка присутствия пользователя
async def check_presence(user_id, date):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM presence WHERE user_id = ? AND date = ?", (user_id, date)) as cursor:
            row = await cursor.fetchone()
            return row is not None

# Отметить пользователя как присутствующего
async def mark_present(user_id, date):
    async with aiosqlite.connect(DB_NAME) as db:
        if not await check_presence(user_id, date):
            await db.execute("INSERT INTO presence (user_id, date) VALUES (?, ?)", (user_id, date))
            await db.commit()

# Получить список присутствующих и отсутствующих
async def get_presence_report(date):
    async with aiosqlite.connect(DB_NAME) as db:
        # Получаем всех пользователей
        users = await db.execute_fetchall("SELECT id, name FROM users")
        present_users = []
        absent_users = []

        for user_id, name in users:
            if await check_presence(user_id, date):
                present_users.append(name)
            else:
                absent_users.append(name)

        return present_users, absent_users

# Генерация таблицы присутствия в формате Markdown
async def generate_presence_table(date):
    async with aiosqlite.connect(DB_NAME) as db:
        # Получаем всех пользователей
        users = await db.execute_fetchall("SELECT id, name FROM users")
        table = ["| Имя       | Присутствие |"]
        table.append("| --------- | ----------- |")

        for user_id, name in users:
            if await check_presence(user_id, date):
                table.append(f"| {name} | ✅          |")
            else:
                table.append(f"| {name} | ❌          |")

        return "\n".join(table)