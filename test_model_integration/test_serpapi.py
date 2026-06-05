import requests

GEMINI_API_KEY = "AIzaSyDtTUF9bm0ggtJS7BqMcj_7TxRbLHp8rdo"  # получите бесплатно на aistudio.google.com


def ask_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Ошибка: {response.text}"


# Использование
print(ask_gemini("Сможешь ли ты проанализировать текст речи?"))