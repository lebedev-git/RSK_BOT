from dataclasses import dataclass
from environs import Env
import os

@dataclass
class Config:
    BOT_TOKEN: str
    GROUP_CHAT_ID: int
    DATABASE_URL: str
    OPENROUTER_API_KEY: str
    MORNING_REPORT_TIME: str = "06:30"
    EVENING_REPORT_TIME: str = "18:00"

    @classmethod
    def load(cls):
        env = Env()
        env.read_env()

        # Для Railway используем переменные окружения
        if os.getenv('RAILWAY_ENVIRONMENT'):
            # Проверяем наличие всех необходимых переменных
            required_vars = ['PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE']
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            
            if missing_vars:
                print(f"Missing environment variables: {', '.join(missing_vars)}")
                # Если переменные отсутствуют, используем SQLite
                return cls(
                    BOT_TOKEN=env.str("BOT_TOKEN"),
                    GROUP_CHAT_ID=env.int("GROUP_CHAT_ID"),
                    DATABASE_URL="sqlite+aiosqlite:///bot_database.db",
                    OPENROUTER_API_KEY=env.str("OPENROUTER_API_KEY")
                )
            
            # Если все переменные есть, используем PostgreSQL
            database_url = f"postgresql+asyncpg://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
        else:
            # Для локальной разработки используем SQLite
            database_url = "sqlite+aiosqlite:///bot_database.db"
        
        return cls(
            BOT_TOKEN=env.str("BOT_TOKEN"),
            GROUP_CHAT_ID=env.int("GROUP_CHAT_ID"),
            DATABASE_URL=env.str("DATABASE_URL", database_url),
            OPENROUTER_API_KEY=env.str("OPENROUTER_API_KEY")
        )

def load_config() -> Config:
    return Config.load()