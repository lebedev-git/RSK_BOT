import json
import aiohttp
from config import load_config

config = load_config()

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
            "HTTP-Referer": "https://github.com/lebedev-git/RSK_BOT",
            "X-Title": "RSK Bot"
        }
        
        data = {
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                response_text = await response.text()
                print(f"Response status: {response.status}")
                print(f"Response text: {response_text}")
                
                if response.status == 200:
                    result = json.loads(response_text)
                    return result['choices'][0]['message']['content']
                else:
                    print(f"Error: {response.status}")
                    return "Извините, произошла ошибка."
                    
    except Exception as e:
        print(f"Error: {e}")
        return "Извините, произошла ошибка." 