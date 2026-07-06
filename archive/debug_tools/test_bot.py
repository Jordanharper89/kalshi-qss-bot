import os
from dotenv import load_dotenv
import requests

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")

print("TOKEN FOUND:", bool(token))

url = f"https://api.telegram.org/bot{token}/getMe"

response = requests.get(url)

print(response.json())