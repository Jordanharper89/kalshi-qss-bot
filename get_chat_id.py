import requests

BOT_TOKEN = "8616054195:AAGUVPgiP1HPn5F93MDzFIUVnFfth9PchOE"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

response = requests.get(url)

print(response.json())