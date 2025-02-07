import json
import aiohttp
from config import load_config

config = load_config()

# Используем DeepSeek вместо OpenRouter
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "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"  # Ваш API ключ
MODEL = "deepseek-chat"

# Системный промпт для настройки поведения бота
SYSTEM_PROMPT = """👋 Привет! Я твой помощник. Чем могу помочь сегодня?😊"""

def process_content(content: str) -> str:
    return content.replace('<think>', '').replace('</think>', '')

async def get_ai_response(message: str) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Вы - помощник для Telegram бота."},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    response_text = await response.text()
                    print(f"Error: {response.status} - {response_text}")
                    return "Извините, произошла ошибка при обработке запроса."
                    
    except Exception as e:
        print(f"Error in AI service: {str(e)}")
        return "Извините, сервис временно недоступен." 