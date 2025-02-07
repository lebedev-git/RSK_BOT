import json
import aiohttp
import os
from environs import Env

env = Env()
env.read_env()

# Получаем API ключ из переменных окружения
API_KEY = env.str("OPENROUTER_API_KEY", "")
MODEL = "deepseek/deepseek-r1"

# Системный промпт для настройки поведения бота
SYSTEM_PROMPT = """👋 Привет! Я твой помощник. Чем могу помочь сегодня?😊"""

def process_content(content: str) -> str:
    return content.replace('<think>', '').replace('</think>', '')

async def get_ai_response(message: str) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/lebedev-git',
            'X-Title': 'RSK Bot'
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Вы - помощник для Telegram бота."},
                {"role": "user", "content": message}
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                print(f"Response status: {response.status}")
                response_text = await response.text()
                print(f"Response body: {response_text}")
                
                if response.status == 200:
                    result = json.loads(response_text)
                    return result['choices'][0]['message']['content']
                else:
                    return "Извините, произошла ошибка при обработке запроса."
                    
    except Exception as e:
        print(f"Error: {e}")
        return "Извините, произошла ошибка при обработке запроса." 