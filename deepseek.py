import requests
import json

API_KEY = "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"

def get_ai_response(message: str) -> str:
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/lebedev-git/RSK_BOT",
                "X-Title": "RSK Bot"
            },
            json={
                "model": "deepseek/deepseek-r1",
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Error: {response.status_code}")
            return "Извините, произошла ошибка."
            
    except Exception as e:
        print(f"Error: {e}")
        return "Извините, произошла ошибка."

# Пример использования
if __name__ == "__main__":
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == 'exit':
            break
        response = get_ai_response(user_input)
        print(f"AI: {response}")