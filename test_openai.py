from dotenv import load_dotenv
import requests
import os

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    print("❗ OPENROUTER_API_KEY missing in .env")
else:
    print("🚀 Testing OpenRouter with requests...")
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions ",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "F.R.I.D.A.Y."
        },
        json={
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": "Say hello"}]
        }
    )
    if res.status_code == 200:
        print("✅ Success! Connected to OpenRouter.")
        print("Reply:", res.json()['choices'][0]['message']['content'])
    else:
        print("❌ Error:", res.status_code, res.text)