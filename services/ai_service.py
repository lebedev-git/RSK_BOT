import json
import aiohttp

API_KEY = "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"
MODEL = "deepseek/deepseek-r1"

# Системный промпт для настройки поведения бота
SYSTEM_PROMPT = """👋 Привет! Я твой помощник. Чем могу помочь сегодня?😊"""

def process_content(content: str) -> str:
    return content.replace('<think>', '').replace('</think>', '')

async def get_ai_response(message: str) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-username",  # Для OpenRouter статистики
            "X-Title": "RSK Bot"  # Название вашего бота
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "stream": False,
            "temperature": 0.5,  # Снизили для более четких ответов
            "max_tokens": 1000,  # Уменьшили для скорости
            "top_p": 0.7,  # Снизили для более предсказуемых ответов
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
                    print("Ошибка авторизации в OpenRouter API. Проверьте токен.")
                    return "Извините, у меня проблемы с доступом к AI. Попробуйте позже."
                else:
                    print(f"Ошибка API: {response.status}")
                    error_text = await response.text()
                    print(error_text)
                    return "Произошла ошибка при обработке запроса. Попробуйте позже."
                    
    except Exception as e:
        print(f"Ошибка при получении ответа от AI: {e}")
        return "Извините, произошла ошибка при обработке запроса. Попробуйте позже." 