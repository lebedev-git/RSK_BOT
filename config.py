from dataclasses import dataclass
from environs import Env

@dataclass
class Config:
    BOT_TOKEN: str
    GROUP_CHAT_ID: int
    DATABASE_URL: str  # Heroku предоставит этот URL
    PENALTY_POINTS: int = 10
    MORNING_REPORT_TIME: str = "06:30"
    EVENING_REPORT_TIME: str = "18:00"

def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(
        BOT_TOKEN=env.str("BOT_TOKEN"),
        GROUP_CHAT_ID=env.int("GROUP_CHAT_ID"),
        DATABASE_URL=env.str("DATABASE_URL", "").replace("postgres://", "postgresql://"),  # Фикс для Heroku
    )