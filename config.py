from dataclasses import dataclass
from environs import Env
import os

@dataclass
class Config:
    BOT_TOKEN: str
    GROUP_CHAT_ID: int
    DATABASE_URL: str
    MORNING_REPORT_TIME: str = "06:30"
    EVENING_REPORT_TIME: str = "18:00"

    @classmethod
    def load(cls):
        env = Env()
        env.read_env()

        # Для локальной разработки используем SQLite
        if not os.getenv('RAILWAY_ENVIRONMENT'):
            return cls(
                BOT_TOKEN=env.str("BOT_TOKEN"),
                GROUP_CHAT_ID=env.int("GROUP_CHAT_ID"),
                DATABASE_URL="sqlite+aiosqlite:///bot_database.db"
            )
        
        # Для Railway используем PostgreSQL
        pg_host = env.str("PGHOST")
        pg_port = env.str("PGPORT")
        pg_user = env.str("PGUSER")
        pg_pass = env.str("PGPASSWORD")
        pg_db = env.str("PGDATABASE")
        
        database_url = f"postgresql+asyncpg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        
        return cls(
            BOT_TOKEN=env.str("BOT_TOKEN"),
            GROUP_CHAT_ID=env.int("GROUP_CHAT_ID"),
            DATABASE_URL=database_url
        )

def load_config() -> Config:
    return Config.load()