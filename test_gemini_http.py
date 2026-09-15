import requests

from config import GEMINI_API_KEY

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.0-flash:generateContent"
)

headers = {
    "Content-Type": "application/json"
}

params = {
    "key": GEMINI_API_KEY
}

data = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Translate to Arabic: Federal Reserve leaves interest rates unchanged."
                }
            ]
        }
    ]
}

response = requests.post(
    url,
    headers=headers,
    params=params,
    json=data,
    timeout=60
)

print(response.status_code)
print(response.text)

