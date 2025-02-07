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
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/lebedev-git',
            'X-Title': 'RSK Bot',
            'OpenAI-Organization': 'lebedev-git'
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
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    print(f"Error {response.status}: {error_text}")
                    return "Извините, произошла ошибка при обработке запроса."
                    
    except Exception as e:
        print(f"Error: {e}")
        return "Извините, произошла ошибка при обработке запроса." 