import json
import aiohttp

API_KEY = "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"  # Убедитесь, что токен актуален
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
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9,
            "frequency_penalty": 0.3,
            "presence_penalty": 0.3
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    return process_content(content)
                elif response.status == 401:
                    print(f"Ошибка авторизации: {await response.text()}")
                    return "Извините, у меня проблемы с доступом. Попробуйте позже."
                else:
                    print(f"Ошибка API: {response.status}")
                    return "Произошла ошибка при обработке запроса. Попробуйте позже."
                    
    except Exception as e:
        print(f"Ошибка при получении ответа от AI: {e}")
        return "Извините, произошла ошибка при обработке запроса. Попробуйте позже." 