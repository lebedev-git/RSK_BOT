import json
import aiohttp
import os
from config import load_config

config = load_config()
API_KEY = config.OPENROUTER_API_KEY
MODEL = "openai/gpt-3.5-turbo"

# Системный промпт для настройки поведения бота
SYSTEM_PROMPT = """👋 Привет! Я твой помощник. Чем могу помочь сегодня?😊"""

def process_content(content: str) -> str:
    return content.replace('<think>', '').replace('</think>', '')

async def get_ai_response(message: str) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Максимально простые заголовки
        headers = {
            "Authorization": "Bearer " + API_KEY.strip(),
            "Content-Type": "application/json"
        }
        
        # Простой запрос
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": message}]
        }

        print(f"API Key: {API_KEY}")  # Выведем полный ключ для проверки
        print(f"Request URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                response_text = await response.text()
                print(f"Response Status: {response.status}")
                print(f"Response Body: {response_text}")
                
                if response.status == 200:
                    result = json.loads(response_text)
                    return result['choices'][0]['message']['content']
                elif response.status == 401:
                    print(f"API Key being used: {API_KEY}")
                    return "Ошибка авторизации. Пожалуйста, проверьте API ключ."
                else:
                    return f"Ошибка {response.status}: {response_text}"
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Ошибка: {str(e)}" 